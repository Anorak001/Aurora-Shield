"""
Prometheus integration for metrics collection.
"""

import time
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class PrometheusIntegration:
    """Integration with Prometheus for metrics export."""
    
    def __init__(self, config=None):
        """
        Initialize Prometheus integration.
        
        Args:
            config (dict): Configuration parameters
        """
        self.config = config or {}
        self.metrics = defaultdict(lambda: {'value': 0, 'timestamp': time.time()})
        self.counters = defaultdict(int)
        self.histograms = defaultdict(list)
        
    def gauge(self, name, value, labels=None):
        """
        Record a gauge metric.
        
        Args:
            name (str): Metric name
            value (float): Metric value
            labels (dict): Optional labels
        """
        key = self._make_key(name, labels)
        self.metrics[key] = {
            'type': 'gauge',
            'value': value,
            'timestamp': time.time(),
            'labels': labels or {}
        }
    
    def counter(self, name, increment=1, labels=None):
        """
        Increment a counter metric.
        
        Args:
            name (str): Metric name
            increment (int): Amount to increment
            labels (dict): Optional labels
        """
        key = self._make_key(name, labels)
        self.counters[key] += increment
        self.metrics[key] = {
            'type': 'counter',
            'value': self.counters[key],
            'timestamp': time.time(),
            'labels': labels or {}
        }
    
    def histogram(self, name, value, labels=None):
        """
        Record a histogram observation.
        
        Args:
            name (str): Metric name
            value (float): Observed value
            labels (dict): Optional labels
        """
        key = self._make_key(name, labels)
        self.histograms[key].append(value)
        
        # Keep only recent observations (last 1000)
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
        
        self.metrics[key] = {
            'type': 'histogram',
            'count': len(self.histograms[key]),
            'sum': sum(self.histograms[key]),
            'timestamp': time.time(),
            'labels': labels or {}
        }
    
    def _make_key(self, name, labels):
        """Create a unique key for metric with labels."""
        if not labels:
            return name
        label_str = ','.join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"
    
    def export_metrics(self):
        """
        Export metrics in Prometheus text format.
        
        Returns:
            str: Metrics in Prometheus format
        """
        lines = []
        
        for key, metric in self.metrics.items():
            metric_type = metric['type']
            value = metric['value']
            
            if metric_type == 'counter':
                lines.append(f"# TYPE {key.split('{')[0]} counter")
            elif metric_type == 'gauge':
                lines.append(f"# TYPE {key.split('{')[0]} gauge")
            elif metric_type == 'histogram':
                lines.append(f"# TYPE {key.split('{')[0]} histogram")
                lines.append(f"{key}_count {metric['count']}")
                lines.append(f"{key}_sum {metric['sum']}")
                continue
            
            lines.append(f"{key} {value}")
        
        return '\n'.join(lines)
    
    def record_request(self, status_code, duration):
        """Record HTTP request metrics."""
        self.counter('aurora_shield_requests_total', labels={'status': str(status_code)})
        self.histogram('aurora_shield_request_duration_seconds', duration)
    
    def record_attack(self, attack_type):
        """Record attack detection."""
        self.counter('aurora_shield_attacks_total', labels={'type': attack_type})
    
    def record_mitigation(self, action):
        """Record mitigation action."""
        self.counter('aurora_shield_mitigations_total', labels={'action': action})
    
    def get_stats(self):
        """Get integration statistics."""
        return {
            'total_metrics': len(self.metrics),
            'counters': len(self.counters),
            'histograms': len(self.histograms)
        }
