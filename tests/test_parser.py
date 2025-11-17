"""
Unit tests for the CNPJ parser module.

Tests CNPJ validation, extraction, and formatting.
"""

import pytest
from scraper.parser import (
    validate_cnpj,
    format_cnpj,
    extract_cnpj_from_text,
    find_valid_cnpj,
    find_all_valid_cnpjs
)


class TestValidateCNPJ:
    """Tests for CNPJ validation."""
    
    def test_valid_cnpj_formatted(self):
        """Test validation of valid formatted CNPJ."""
        assert validate_cnpj("11.222.333/0001-81") == True
    
    def test_valid_cnpj_raw(self):
        """Test validation of valid raw CNPJ."""
        assert validate_cnpj("11222333000181") == True
    
    def test_invalid_cnpj_wrong_check_digit(self):
        """Test validation fails for wrong check digit."""
        assert validate_cnpj("11.222.333/0001-99") == False
    
    def test_invalid_cnpj_too_short(self):
        """Test validation fails for too short CNPJ."""
        assert validate_cnpj("11.222.333/0001") == False
    
    def test_invalid_cnpj_too_long(self):
        """Test validation fails for too long CNPJ."""
        assert validate_cnpj("11.222.333/0001-811") == False
    
    def test_invalid_cnpj_all_same_digit(self):
        """Test validation fails for CNPJ with all same digits."""
        assert validate_cnpj("11.111.111/1111-11") == False
        assert validate_cnpj("00000000000000") == False
    
    def test_invalid_cnpj_empty(self):
        """Test validation fails for empty string."""
        assert validate_cnpj("") == False
    
    def test_invalid_cnpj_none(self):
        """Test validation fails for None."""
        assert validate_cnpj(None) == False
    
    def test_valid_real_cnpj_examples(self):
        """Test validation with real CNPJ examples."""
        assert validate_cnpj("00.000.000/0001-91") == True
        assert validate_cnpj("11.222.333/0001-81") == True


class TestFormatCNPJ:
    """Tests for CNPJ formatting."""
    
    def test_format_raw_cnpj(self):
        """Test formatting raw CNPJ."""
        result = format_cnpj("11222333000181")
        assert result == "11.222.333/0001-81"
    
    def test_format_already_formatted_cnpj(self):
        """Test formatting already formatted CNPJ."""
        result = format_cnpj("11.222.333/0001-81")
        assert result == "11.222.333/0001-81"
    
    def test_format_partially_formatted_cnpj(self):
        """Test formatting partially formatted CNPJ."""
        result = format_cnpj("11222333/0001-81")
        assert result == "11.222.333/0001-81"
    
    def test_format_invalid_length(self):
        """Test formatting returns None for invalid length."""
        assert format_cnpj("123") is None
        assert format_cnpj("123456789012345") is None
    
    def test_format_empty_string(self):
        """Test formatting returns None for empty string."""
        assert format_cnpj("") is None
    
    def test_format_none(self):
        """Test formatting returns None for None."""
        assert format_cnpj(None) is None


class TestExtractCNPJ:
    """Tests for CNPJ extraction from text."""
    
    def test_extract_single_formatted_cnpj(self):
        """Test extracting single formatted CNPJ."""
        text = "A empresa tem CNPJ 11.222.333/0001-81 registrado."
        result = extract_cnpj_from_text(text)
        assert len(result) == 1
        assert "11.222.333/0001-81" in result
    
    def test_extract_single_raw_cnpj(self):
        """Test extracting single raw CNPJ."""
        text = "CNPJ: 11222333000181"
        result = extract_cnpj_from_text(text)
        assert len(result) == 1
        assert "11.222.333/0001-81" in result
    
    def test_extract_multiple_cnpjs(self):
        """Test extracting multiple CNPJs."""
        text = "Empresa A: 11.222.333/0001-81 e Empresa B: 00.000.000/0001-91"
        result = extract_cnpj_from_text(text)
        assert len(result) == 2
    
    def test_extract_no_cnpj(self):
        """Test extraction returns empty list when no CNPJ found."""
        text = "Esta é uma empresa sem CNPJ mencionado."
        result = extract_cnpj_from_text(text)
        assert len(result) == 0
    
    def test_extract_from_empty_text(self):
        """Test extraction from empty text."""
        result = extract_cnpj_from_text("")
        assert len(result) == 0
    
    def test_extract_mixed_formats(self):
        """Test extracting CNPJs in mixed formats."""
        text = "CNPJ formatado: 11.222.333/0001-81 e CNPJ raw: 00000000000191"
        result = extract_cnpj_from_text(text)
        assert len(result) == 2


class TestFindValidCNPJ:
    """Tests for finding valid CNPJ in text."""
    
    def test_find_valid_cnpj_in_text(self):
        """Test finding valid CNPJ in text."""
        text = "A empresa possui CNPJ 11.222.333/0001-81 ativo."
        result = find_valid_cnpj(text)
        assert result == "11.222.333/0001-81"
    
    def test_find_valid_cnpj_ignores_invalid(self):
        """Test that invalid CNPJs are ignored."""
        text = "CNPJ inválido: 11.222.333/0001-99 e válido: 11.222.333/0001-81"
        result = find_valid_cnpj(text)
        assert result == "11.222.333/0001-81"
    
    def test_find_valid_cnpj_returns_none_when_not_found(self):
        """Test returns None when no valid CNPJ found."""
        text = "Empresa sem CNPJ válido: 11.222.333/0001-99"
        result = find_valid_cnpj(text)
        assert result is None


class TestFindAllValidCNPJs:
    """Tests for finding all valid CNPJs in text."""
    
    def test_find_all_valid_cnpjs(self):
        """Test finding all valid CNPJs."""
        text = "Empresa A: 11.222.333/0001-81 e Empresa B: 00.000.000/0001-91"
        result = find_all_valid_cnpjs(text)
        assert len(result) == 2
        assert "11.222.333/0001-81" in result
        assert "00.000.000/0001-91" in result
    
    def test_find_all_valid_cnpjs_filters_invalid(self):
        """Test that invalid CNPJs are filtered out."""
        text = "Válido: 11.222.333/0001-81, Inválido: 11.111.111/1111-11, Válido: 00.000.000/0001-91"
        result = find_all_valid_cnpjs(text)
        assert len(result) == 2
        assert "11.111.111/1111-11" not in result
    
    def test_find_all_valid_cnpjs_deduplicates(self):
        """Test that duplicate CNPJs are removed."""
        text = "CNPJ: 11.222.333/0001-81 e novamente: 11.222.333/0001-81"
        result = find_all_valid_cnpjs(text)
        assert len(result) == 1
    
    def test_find_all_valid_cnpjs_empty_list_when_none_found(self):
        """Test returns empty list when no valid CNPJs found."""
        text = "Empresa sem CNPJ válido"
        result = find_all_valid_cnpjs(text)
        assert len(result) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
