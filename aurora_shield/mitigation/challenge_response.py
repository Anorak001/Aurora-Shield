"""
Challenge-response system for verifying legitimate users.
Implements CAPTCHA-like verification and JavaScript challenges.
"""

import hashlib
import time
import secrets
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class ChallengeResponse:
    """Challenge-response verification system."""
    
    def __init__(self, config=None):
        """
        Initialize challenge-response system.
        
        Args:
            config (dict): Configuration parameters
        """
        self.config = config or {}
        self.challenges = {}
        self.verified_clients = defaultdict(lambda: {'verified': False, 'timestamp': 0})
        self.challenge_timeout = self.config.get('challenge_timeout', 300)  # 5 minutes
        
    def generate_challenge(self, client_id):
        """
        Generate a challenge for a client.
        
        Args:
            client_id (str): Unique client identifier
            
        Returns:
            dict: Challenge data
        """
        # Generate random challenge
        nonce = secrets.token_hex(16)
        timestamp = time.time()
        
        challenge_data = {
            'nonce': nonce,
            'timestamp': timestamp,
            'client_id': client_id,
            'expires': timestamp + self.challenge_timeout
        }
        
        # Store challenge
        challenge_key = hashlib.sha256(f"{client_id}{nonce}".encode()).hexdigest()
        self.challenges[challenge_key] = challenge_data
        
        logger.info(f"Generated challenge for client {client_id}")
        
        return {
            'challenge_key': challenge_key,
            'nonce': nonce,
            'type': 'proof_of_work',
            'instructions': 'Compute SHA256(nonce + answer) where answer starts with "0000"'
        }
    
    def verify_response(self, challenge_key, response):
        """
        Verify a challenge response.
        
        Args:
            challenge_key (str): The challenge identifier
            response (str): Client's response
            
        Returns:
            dict: Verification result
        """
        if challenge_key not in self.challenges:
            return {
                'verified': False,
                'reason': 'Invalid or expired challenge'
            }
        
        challenge = self.challenges[challenge_key]
        
        # Check expiration
        if time.time() > challenge['expires']:
            del self.challenges[challenge_key]
            return {
                'verified': False,
                'reason': 'Challenge expired'
            }
        
        # Verify response (simple proof of work)
        nonce = challenge['nonce']
        test_hash = hashlib.sha256(f"{nonce}{response}".encode()).hexdigest()
        
        if test_hash.startswith('0000'):
            # Mark client as verified
            client_id = challenge['client_id']
            self.verified_clients[client_id] = {
                'verified': True,
                'timestamp': time.time()
            }
            del self.challenges[challenge_key]
            
            logger.info(f"Client {client_id} successfully verified")
            
            return {
                'verified': True,
                'client_id': client_id
            }
        else:
            return {
                'verified': False,
                'reason': 'Invalid response'
            }
    
    def is_verified(self, client_id):
        """
        Check if a client is verified.
        
        Args:
            client_id (str): Client identifier
            
        Returns:
            bool: Whether client is verified
        """
        client = self.verified_clients.get(client_id)
        if not client or not client['verified']:
            return False
        
        # Check if verification is still valid (1 hour)
        if time.time() - client['timestamp'] > 3600:
            client['verified'] = False
            return False
        
        return True
    
    def get_stats(self):
        """Get challenge system statistics."""
        active_challenges = sum(1 for c in self.challenges.values() if time.time() < c['expires'])
        return {
            'active_challenges': active_challenges,
            'verified_clients': sum(1 for c in self.verified_clients.values() if c['verified']),
            'total_challenges_issued': len(self.challenges)
        }
