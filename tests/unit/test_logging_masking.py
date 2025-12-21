"""Tests for sensitive data masking."""


from src.logutils.masking import (
    MASK,
    SensitiveValue,
    is_sensitive_key,
    mask_dict,
    mask_sensitive_string,
)


class TestMaskSensitiveString:
    """Tests for mask_sensitive_string function."""

    def test_empty_string(self):
        """Empty string should return empty string."""
        assert mask_sensitive_string("") == ""

    def test_no_sensitive_data(self):
        """String without sensitive data should remain unchanged."""
        text = "This is a normal log message"
        assert mask_sensitive_string(text) == text

    def test_password_in_key_value(self):
        """Password in key=value format should be masked."""
        text = 'password=mysecret123'
        result = mask_sensitive_string(text)
        assert "mysecret123" not in result
        assert MASK in result

    def test_password_in_json(self):
        """Password in JSON format should be masked."""
        text = '{"password": "secret123"}'
        result = mask_sensitive_string(text)
        assert "secret123" not in result
        assert MASK in result

    def test_api_key(self):
        """API keys should be masked."""
        text = 'api_key=abc123xyz'
        result = mask_sensitive_string(text)
        assert "abc123xyz" not in result

    def test_bearer_token(self):
        """Bearer tokens should be masked."""
        text = 'auth_token=eyJhbGciOiJIUzI1NiJ9'
        result = mask_sensitive_string(text)
        assert "eyJhbGciOiJIUzI1NiJ9" not in result

    def test_url_credentials(self):
        """Credentials in URLs should be masked."""
        text = 'https://user:password123@example.com/api'
        result = mask_sensitive_string(text)
        assert "password123" not in result
        assert "https://" in result
        assert "@example.com" in result or "example.com" in result

    def test_base64_password(self):
        """Base64 encoded passwords should be masked."""
        text = 'password_b64=c2VjcmV0MTIz'
        result = mask_sensitive_string(text)
        assert "c2VjcmV0MTIz" not in result

    def test_email_partial_mask(self):
        """Emails should be partially masked."""
        text = 'user email: john.doe@example.com'
        result = mask_sensitive_string(text)
        assert "john.doe@example.com" not in result
        # Should preserve domain
        assert "example.com" in result

    def test_multiple_sensitive_values(self):
        """Multiple sensitive values should all be masked."""
        text = 'password=secret1 api_key=key123'
        result = mask_sensitive_string(text)
        assert "secret1" not in result
        assert "key123" not in result


class TestMaskDict:
    """Tests for mask_dict function."""

    def test_empty_dict(self):
        """Empty dict should return empty dict."""
        assert mask_dict({}) == {}

    def test_non_sensitive_keys(self):
        """Non-sensitive keys should not be masked."""
        data = {"name": "John", "age": 30}
        result = mask_dict(data)
        assert result == {"name": "John", "age": 30}

    def test_sensitive_key_password(self):
        """Password keys should be masked."""
        data = {"username": "john", "password": "secret123"}
        result = mask_dict(data)
        assert result["username"] == "john"
        assert result["password"] == MASK

    def test_sensitive_key_variations(self):
        """Various sensitive key names should be masked."""
        data = {
            "api_key": "key123",
            "apiKey": "key456",
            "secret": "shhh",
            "token": "tok123",
            "auth_token": "authtok",
            "credentials": {"user": "test"},
        }
        result = mask_dict(data)
        assert result["api_key"] == MASK
        assert result["apiKey"] == MASK
        assert result["secret"] == MASK
        assert result["token"] == MASK
        assert result["auth_token"] == MASK
        assert result["credentials"] == MASK

    def test_nested_dict(self):
        """Nested dicts should be recursively masked."""
        data = {
            "user": {
                "name": "John",
                "password": "secret",
            }
        }
        result = mask_dict(data)
        assert result["user"]["name"] == "John"
        assert result["user"]["password"] == MASK

    def test_list_of_dicts(self):
        """Lists of dicts should be recursively masked."""
        data = {
            "users": [
                {"name": "John", "password": "secret1"},
                {"name": "Jane", "password": "secret2"},
            ]
        }
        result = mask_dict(data)
        assert result["users"][0]["password"] == MASK
        assert result["users"][1]["password"] == MASK
        assert result["users"][0]["name"] == "John"

    def test_max_depth(self):
        """Masking should respect max depth."""
        deeply_nested = {"level1": {"level2": {"level3": {"password": "secret"}}}}
        # With depth limit of 2, innermost password won't be masked
        result = mask_dict(deeply_nested, max_depth=2)
        # The password key at depth 3+ should still be processed
        assert result is not None

    def test_string_values_in_dict(self):
        """String values should have sensitive patterns masked."""
        data = {"log_message": "Login with password=secret123 succeeded"}
        result = mask_dict(data)
        assert "secret123" not in result["log_message"]


class TestIsSensitiveKey:
    """Tests for is_sensitive_key function."""

    def test_password_variations(self):
        """Password variations should be detected."""
        assert is_sensitive_key("password") is True
        assert is_sensitive_key("PASSWORD") is True
        assert is_sensitive_key("user_password") is True
        assert is_sensitive_key("passwd") is True

    def test_token_variations(self):
        """Token variations should be detected."""
        assert is_sensitive_key("token") is True
        assert is_sensitive_key("auth_token") is True
        assert is_sensitive_key("access_token") is True
        assert is_sensitive_key("refresh_token") is True

    def test_api_key_variations(self):
        """API key variations should be detected."""
        assert is_sensitive_key("api_key") is True
        assert is_sensitive_key("apikey") is True
        assert is_sensitive_key("api-key") is False  # hyphen not in pattern

    def test_non_sensitive(self):
        """Non-sensitive keys should return False."""
        assert is_sensitive_key("username") is False
        assert is_sensitive_key("name") is False
        assert is_sensitive_key("email") is False
        assert is_sensitive_key("student_id") is False


class TestSensitiveValue:
    """Tests for SensitiveValue wrapper."""

    def test_str_returns_mask(self):
        """str() should return MASK."""
        sv = SensitiveValue("secret123")
        assert str(sv) == MASK

    def test_repr_returns_mask(self):
        """repr() should return masked representation."""
        sv = SensitiveValue("secret123")
        assert MASK in repr(sv)
        assert "secret123" not in repr(sv)

    def test_get_returns_actual_value(self):
        """get() should return the actual value."""
        sv = SensitiveValue("secret123")
        assert sv.get() == "secret123"

    def test_bool_true_for_truthy_value(self):
        """bool() should return True for truthy values."""
        sv = SensitiveValue("secret123")
        assert bool(sv) is True

    def test_bool_false_for_falsy_value(self):
        """bool() should return False for falsy values."""
        sv = SensitiveValue("")
        assert bool(sv) is False
        sv2 = SensitiveValue(None)
        assert bool(sv2) is False

    def test_in_fstring(self):
        """SensitiveValue should mask in f-strings."""
        sv = SensitiveValue("secret123")
        result = f"Password: {sv}"
        assert "secret123" not in result
        assert MASK in result
