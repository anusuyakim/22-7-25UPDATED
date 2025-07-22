# download_model.py

import os
import datetime
from typing import Dict, Optional, Tuple
import re
import google.generativeai as genai # --- NEW: Import Google's library

# --- NEW: This is the context we will feed the LLM so it knows about YOUR website ---
VENDHAN_INFO_TECH_CONTEXT = """
You are the "Vendhan AI Assistant", a helpful and professional AI representing Vendhan Info Tech.
Your primary goal is to answer user questions accurately.
First, use your internal knowledge about Vendhan Info Tech. If the user asks a general question,
use your broader knowledge to answer it.

Key information about Vendhan Info Tech:
- Name: Vendhan Info Tech
- Core Identity: A pioneering, women-led IT solutions company.
- Mission: To empower businesses with innovative technology and champion women's leadership in tech.
- Key Services: AI & Machine Learning, Digital Transformation, Custom Software Development (Web & Mobile), and Data & Cybersecurity.
- Industries Served: Healthcare, Financial Services, E-commerce, Manufacturing, Education, and Government.
- Leadership: CEO & Founder is Renugadevi; CTO is Ramprabhu.
- How to Apply for a job: Users must visit the "Careers" section on the website. The direct link is #careers.
- How to Contact: Users should use the form on the "Contact" section of the website. The direct link is #contact.
"""

class VendhanInfoTechChatbot:
    def __init__(self):
        """
        Initializes the Hybrid Chatbot.
        It configures the Google Gemini API and sets up the rule-based knowledge.
        """
        self.conversation_history = []

        # --- NEW: Configure the Google Gemini API ---
        try:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                print("⚠️ WARNING: GOOGLE_API_KEY not found. The advanced chatbot features will be disabled.")
                self.llm = None
            else:
                genai.configure(api_key=api_key)
                self.llm = genai.GenerativeModel('gemini-1.5-flash-latest')
                print("✅ Google Gemini Pro model initialized successfully.")
        except Exception as e:
            print(f"❌ ERROR: Failed to initialize Google Gemini Pro: {e}")
            self.llm = None

        # This is our "Fast Lane" knowledge base for quick, specific answers
        self.rule_based_knowledge = {
            'careers': "That's fantastic! We are always looking for passionate and talented people to join our mission. You can fill out the application form and upload your resume directly on our careers page.<br><br><a href=\"#careers\" class=\"chat-link\">Go to the Careers Section</a>",
            'contact': "We'd love to hear from you! The best way to discuss your project is by filling out our contact form.<br><br><a href=\"#contact\" class=\"chat-link\">Go to the Contact Section</a>",
            'greeting': "Hello! I'm the Vendhan AI Assistant. I can tell you about our company or answer general questions. How can I help?",
            'goodbye': "Thank you for chatting with me! If you have any more questions, feel free to ask. Have a great day!",
        }
        
        # Keywords for the "Fast Lane"
        self.intent_patterns = {
            'careers': [r'\b(apply|join|career|job|position|hiring|work for you|link to apply|employment)\b'],
            'contact': [r'\b(contact|reach|phone|email|address|details|talk to someone|speak with)\b'],
            'greeting': [r'\b(hello|hi|hey|good morning|yo)\b'],
            'goodbye': [r'\b(bye|goodbye|see you|thanks|thank you|that is all|ok thanks)\b']
        }
        
    def load_model(self):
        # This function is now just for confirmation.
        print("Hybrid chatbot system initialized.")
        pass

    def detect_rule_based_intent(self, message: str) -> Optional[str]:
        """Checks if the message matches a simple, fast-lane rule."""
        message_lower = message.lower()
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    return intent
        return None

    # --- NEW: This function calls the Google Gemini API ---
    def query_llm(self, user_message: str) -> str:
        """
        Sends the user's question to the Gemini LLM with context.
        This is the "Expert Lane".
        """
        if not self.llm:
            return "I apologize, but my advanced AI capabilities are currently offline. I can still help with questions about careers or contact information."

        # Combine our website context with the user's question
        prompt = VENDHAN_INFO_TECH_CONTEXT + f"\n\nUser Question: \"{user_message}\"\n\nAnswer:"
        
        try:
            response = self.llm.generate_content(prompt)
            # Add a small disclaimer for user safety and transparency
            disclaimer = "<br><br><small><i>This response is AI-generated.</i></small>"
            return response.text + disclaimer
        except Exception as e:
            print(f"❌ ERROR during Gemini API call: {e}")
            return "I seem to be having trouble connecting to my advanced knowledge base. Please try again in a moment."

    def chat(self, user_message: str) -> Dict:
        """
        The main chat function for the Hybrid model.
        """
        try:
            # 1. Check the "Fast Lane" first
            intent = self.detect_rule_based_intent(user_message)
            
            if intent and intent in self.rule_based_knowledge:
                # If we find a quick rule, use it and we're done.
                response_content = self.rule_based_knowledge[intent]
                confidence = 0.99
            else:
                # 2. If no rule matches, use the "Expert Lane" (LLM)
                print(f"No rule found for '{user_message}'. Escalating to Gemini Pro...")
                intent = "llm_query"
                response_content = self.query_llm(user_message)
                confidence = 0.85 # A bit less confident as it's generated

            return {
                'response': response_content,
                'intent': intent,
                'confidence': confidence,
                'timestamp': datetime.datetime.now().isoformat()
            }
        except Exception as e:
            print(f"❌ ERROR in chat method: {e}")
            return {
                'response': "I apologize, but I've encountered a technical issue. Please try again in a moment.",
                'intent': 'error', 'confidence': 0.0, 'timestamp': datetime.datetime.now().isoformat()
            }

def create_enhanced_chatbot():
    return VendhanInfoTechChatbot()