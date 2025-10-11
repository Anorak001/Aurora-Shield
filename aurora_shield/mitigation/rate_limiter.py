"""
Rate limiting implementation using token bucket algorithm.
"""

import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, config=None):
        """
        Initialize rate limiter.
        
        Args:
            config (dict): Configuration with rate and burst limits
        """
        self.config = config or {}
        self.rate = self.config.get('rate', 10)  # tokens per second
        self.burst = self.config.get('burst', 20)  # max tokens
        self.buckets = defaultdict(lambda: {'tokens': self.burst, 'last_update': time.time()})
        
    def allow_request(self, identifier):
        """
        Check if a request should be allowed.
        
        Args:
            identifier (str): Unique identifier (e.g., IP address)
            
        Returns:
            dict: Decision with allowed status and details
        """
        now = time.time()
        bucket = self.buckets[identifier]
        
        # Refill tokens based on time passed
        time_passed = now - bucket['last_update']
        bucket['tokens'] = min(self.burst, bucket['tokens'] + time_passed * self.rate)
        bucket['last_update'] = now
        
        # Check if we have tokens
        if bucket['tokens'] >= 1:
            bucket['tokens'] -= 1
            return {
                'allowed': True,
                'remaining': int(bucket['tokens']),
                'identifier': identifier
            }
        else:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return {
                'allowed': False,
                'reason': 'Rate limit exceeded',
                'retry_after': int((1 - bucket['tokens']) / self.rate),
                'identifier': identifier
            }
    
    def reset_bucket(self, identifier):
        """Reset token bucket for an identifier."""
        if identifier in self.buckets:
            del self.buckets[identifier]
            
    def get_stats(self):
        """Get rate limiter statistics."""
        return {
            'tracked_identifiers': len(self.buckets),
            'rate_per_second': self.rate,
            'burst_limit': self.burst
        }
