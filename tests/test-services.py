import unittest
from unittest.mock import patch
from investment_analysis.services import InvestmentAnalysisService
import pytest

class TestInvestmentAnalysisService(unittest.TestCase):

    @patch('investment_analysis.services.openai.Client')  # Mock the OpenAI client
    def test_analyze_investment_success(self, mock_openai_client):
        # Configure the mock to return a specific response
        mock_response = type('obj', (object,), {'choices': [type('obj', (object,), {'message': type('obj', (object,), {'content': 'Mock analysis'})})]})
        mock_openai_client.return_value.chat.completions.create.return_value = mock_response

        service = InvestmentAnalysisService(openai_api_key="dummy_key")
        result = service.analyze_investment("Test input")
        self.assertEqual(result, "Mock analysis")

    @patch('investment_analysis.services.openai.Client')
    def test_analyze_investment_api_error(self, mock_openai_client):
        # Configure the mock to raise an exception
        mock_openai_client.return_value.chat.completions.create.side_effect = Exception("API error")

        service = InvestmentAnalysisService(openai_api_key="dummy_key")
        with self.assertRaises(ValueError) as context:
            service.analyze_investment("Test input")
        self.assertTrue("API error" in str(context.exception))
