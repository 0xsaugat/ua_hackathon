from validators import validate_email_address, validate_idn_domain


def test_valid_email_accepts_devanagari_address():
    result = validate_email_address("राम@नेपाल.नेपाल")

    assert result.valid is True
    assert result.normalized_email is not None
    assert result.domain_unicode == "नेपाल.नेपाल"


def test_valid_email_accepts_mixed_script_address():
    result = validate_email_address("pelé@mañana.com")

    assert result.valid is True
    assert result.normalized_email == "pelé@mañana.com"


def test_valid_email_accepts_chinese_idn_address():
    result = validate_email_address("用户@例子.广告")

    assert result.valid is True
    assert result.smtp_utf8 is True


def test_valid_email_accepts_arabic_address():
    result = validate_email_address("اسم@مثال.إختبار")

    assert result.valid is True
    assert result.domain_unicode == "مثال.إختبار"


def test_valid_email_accepts_cyrillic_address():
    result = validate_email_address("почта@пример.рус")

    assert result.valid is True
    assert result.normalized_email is not None


def test_invalid_email_rejects_missing_at_symbol():
    result = validate_email_address("plainaddress")

    assert result.valid is False
    assert result.error_message


def test_invalid_email_rejects_missing_domain():
    result = validate_email_address("राम@")

    assert result.valid is False


def test_invalid_email_rejects_double_dot_domain():
    result = validate_email_address("name@domain..com")

    assert result.valid is False


def test_invalid_email_rejects_space_in_domain():
    result = validate_email_address("name@exa mple.com")

    assert result.valid is False


def test_invalid_email_rejects_broken_unicode_domain():
    result = validate_email_address("user@-example.com")

    assert result.valid is False


def test_domain_validation_accepts_idn_domain():
    valid, normalized_domain, ascii_domain, error = validate_idn_domain("नेपाल.नेपाल")

    assert valid is True
    assert normalized_domain == "नेपाल.नेपाल"
    assert ascii_domain is not None
    assert error is None


def test_domain_validation_rejects_invalid_domain():
    valid, normalized_domain, ascii_domain, error = validate_idn_domain("example..com")

    assert valid is False
    assert normalized_domain is None
    assert ascii_domain is None
    assert error