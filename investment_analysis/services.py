import openai
import logging
import os

class InvestmentAnalysisService:
    def __init__(self, openai_api_key=None):
        self.openai_api_key = openai_api_key or os.environ.get("OPENAI_API_KEY")
        if not self.openai_api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass it to the constructor.")
        self.client = openai.Client(api_key=self.openai_api_key)
        self.system_prompt = "You are an expert on startup investment analysis."

    def analyze_investment(self, user_input):
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_input}
                ]
            )
            return response.choices[0].message.content.strip()
        except openai.APIConnectionError as e:
            logging.error(f"API Connection Error: {e}")
            raise ValueError("Could not connect to the OpenAI API. Please check your internet connection.") from e
        except openai.RateLimitError as e:
            logging.error(f"Rate Limit Error: {e}")
            raise ValueError("OpenAI API rate limit exceeded. Please try again later.") from e
        except Exception as e:
            logging.error(f"OpenAI API call failed: {str(e)}")
            raise ValueError(f"OpenAI API call failed: {str(e)}") from e
