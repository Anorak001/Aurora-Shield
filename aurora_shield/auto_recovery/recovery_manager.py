"""
Auto-recovery manager for handling failover, autoscaling, and traffic redirection.
"""

import logging
import time
from enum import Enum

logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    """Types of recovery actions."""
    FAILOVER = "failover"
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    REDIRECT_TRAFFIC = "redirect_traffic"
    ENABLE_CACHE = "enable_cache"


class RecoveryManager:
    """Manages automatic recovery actions during DDoS attacks."""
    
    def __init__(self, config=None):
        """
        Initialize recovery manager.
        
        Args:
            config (dict): Configuration for recovery thresholds
        """
        self.config = config or {}
        self.active_servers = self.config.get('servers', ['primary'])
        self.current_capacity = 1
        self.max_capacity = self.config.get('max_capacity', 5)
        self.recovery_history = []
        self.traffic_routes = {'default': 'primary'}
        
    def assess_situation(self, metrics):
        """
        Assess the current situation and determine if recovery action is needed.
        
        Args:
            metrics (dict): Current system metrics
            
        Returns:
            dict: Assessment with recommended actions
        """
        cpu_usage = metrics.get('cpu_usage', 0)
        request_rate = metrics.get('request_rate', 0)
        error_rate = metrics.get('error_rate', 0)
        
        actions = []
        priority = 'normal'
        
        # Check for critical conditions
        if error_rate > 0.5:
            actions.append(RecoveryAction.FAILOVER)
            priority = 'critical'
        elif cpu_usage > 80 and self.current_capacity < self.max_capacity:
            actions.append(RecoveryAction.SCALE_UP)
            priority = 'high'
        elif request_rate > 1000:
            actions.append(RecoveryAction.REDIRECT_TRAFFIC)
            actions.append(RecoveryAction.ENABLE_CACHE)
            priority = 'high'
        elif cpu_usage < 30 and self.current_capacity > 1:
            actions.append(RecoveryAction.SCALE_DOWN)
            priority = 'low'
        
        return {
            'actions': [a.value for a in actions],
            'priority': priority,
            'metrics': metrics,
            'timestamp': time.time()
        }
    
    def execute_recovery(self, action, **kwargs):
        """
        Execute a recovery action.
        
        Args:
            action (str or RecoveryAction): Action to execute
            **kwargs: Additional parameters for the action
            
        Returns:
            dict: Result of the action
        """
        if isinstance(action, str):
            action = RecoveryAction(action)
        
        logger.info(f"Executing recovery action: {action.value}")
        
        result = None
        
        if action == RecoveryAction.FAILOVER:
            result = self._execute_failover(**kwargs)
        elif action == RecoveryAction.SCALE_UP:
            result = self._execute_scale_up(**kwargs)
        elif action == RecoveryAction.SCALE_DOWN:
            result = self._execute_scale_down(**kwargs)
        elif action == RecoveryAction.REDIRECT_TRAFFIC:
            result = self._execute_traffic_redirect(**kwargs)
        elif action == RecoveryAction.ENABLE_CACHE:
            result = self._enable_cache(**kwargs)
        
        # Log the action
        self.recovery_history.append({
            'action': action.value,
            'timestamp': time.time(),
            'result': result
        })
        
        return result
    
    def _execute_failover(self, **kwargs):
        """Execute failover to backup server."""
        backup_server = kwargs.get('backup', 'secondary')
        
        if backup_server not in self.active_servers:
            self.active_servers.append(backup_server)
        
        self.traffic_routes['default'] = backup_server
        
        logger.info(f"Failover completed to {backup_server}")
        return {
            'success': True,
            'action': 'failover',
            'new_primary': backup_server
        }
    
    def _execute_scale_up(self, **kwargs):
        """Scale up capacity."""
        if self.current_capacity >= self.max_capacity:
            return {
                'success': False,
                'action': 'scale_up',
                'reason': 'Max capacity reached'
            }
        
        self.current_capacity += 1
        new_server = f"server_{self.current_capacity}"
        self.active_servers.append(new_server)
        
        logger.info(f"Scaled up to {self.current_capacity} instances")
        return {
            'success': True,
            'action': 'scale_up',
            'new_capacity': self.current_capacity,
            'new_server': new_server
        }
    
    def _execute_scale_down(self, **kwargs):
        """Scale down capacity."""
        if self.current_capacity <= 1:
            return {
                'success': False,
                'action': 'scale_down',
                'reason': 'Minimum capacity reached'
            }
        
        removed_server = self.active_servers.pop()
        self.current_capacity -= 1
        
        logger.info(f"Scaled down to {self.current_capacity} instances")
        return {
            'success': True,
            'action': 'scale_down',
            'new_capacity': self.current_capacity,
            'removed_server': removed_server
        }
    
    def _execute_traffic_redirect(self, **kwargs):
        """Redirect traffic to CDN or alternate routes."""
        cdn_endpoint = kwargs.get('cdn', 'cdn.example.com')
        self.traffic_routes['cdn'] = cdn_endpoint
        
        logger.info(f"Traffic redirected to CDN: {cdn_endpoint}")
        return {
            'success': True,
            'action': 'redirect_traffic',
            'cdn_endpoint': cdn_endpoint
        }
    
    def _enable_cache(self, **kwargs):
        """Enable aggressive caching."""
        cache_ttl = kwargs.get('ttl', 3600)
        
        logger.info(f"Aggressive caching enabled with TTL: {cache_ttl}s")
        return {
            'success': True,
            'action': 'enable_cache',
            'cache_ttl': cache_ttl
        }
    
    def get_status(self):
        """Get current recovery system status."""
        return {
            'active_servers': self.active_servers,
            'current_capacity': self.current_capacity,
            'max_capacity': self.max_capacity,
            'traffic_routes': self.traffic_routes,
            'recovery_actions_taken': len(self.recovery_history),
            'recent_actions': self.recovery_history[-5:]
        }
