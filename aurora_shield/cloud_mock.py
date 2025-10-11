"""
Mock cloud provider interface using Boto3-like API.
Simulates cloud operations for testing without actual cloud resources.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class MockEC2:
    """Mock EC2 service for instance management."""
    
    def __init__(self):
        self.instances = {}
        self.instance_counter = 0
    
    def run_instances(self, **kwargs):
        """Launch new instances."""
        count = kwargs.get('MinCount', 1)
        instance_type = kwargs.get('InstanceType', 't2.micro')
        
        new_instances = []
        for _ in range(count):
            self.instance_counter += 1
            instance_id = f"i-{self.instance_counter:08d}"
            instance = {
                'InstanceId': instance_id,
                'InstanceType': instance_type,
                'State': {'Name': 'running'},
                'PublicIpAddress': f"54.{self.instance_counter}.0.1"
            }
            self.instances[instance_id] = instance
            new_instances.append(instance)
        
        logger.info(f"Launched {count} instances")
        return {'Instances': new_instances}
    
    def terminate_instances(self, instance_ids):
        """Terminate instances."""
        for instance_id in instance_ids:
            if instance_id in self.instances:
                self.instances[instance_id]['State']['Name'] = 'terminated'
        logger.info(f"Terminated {len(instance_ids)} instances")
        return {'TerminatingInstances': [self.instances[iid] for iid in instance_ids]}
    
    def describe_instances(self, instance_ids=None):
        """Describe instances."""
        if instance_ids:
            instances = [self.instances[iid] for iid in instance_ids if iid in self.instances]
        else:
            instances = list(self.instances.values())
        return {'Reservations': [{'Instances': instances}]}


class MockELB:
    """Mock Elastic Load Balancer service."""
    
    def __init__(self):
        self.load_balancers = {}
    
    def create_load_balancer(self, name, **kwargs):
        """Create load balancer."""
        lb = {
            'LoadBalancerName': name,
            'DNSName': f"{name}.elb.amazonaws.com",
            'Listeners': kwargs.get('Listeners', []),
            'HealthCheck': kwargs.get('HealthCheck', {})
        }
        self.load_balancers[name] = lb
        logger.info(f"Created load balancer: {name}")
        return lb
    
    def register_instances(self, lb_name, instances):
        """Register instances with load balancer."""
        if lb_name in self.load_balancers:
            self.load_balancers[lb_name]['Instances'] = instances
            logger.info(f"Registered {len(instances)} instances with {lb_name}")
        return {'Instances': instances}
    
    def deregister_instances(self, lb_name, instances):
        """Deregister instances from load balancer."""
        if lb_name in self.load_balancers:
            current = self.load_balancers[lb_name].get('Instances', [])
            self.load_balancers[lb_name]['Instances'] = [
                i for i in current if i not in instances
            ]
            logger.info(f"Deregistered {len(instances)} instances from {lb_name}")


class MockAutoScaling:
    """Mock Auto Scaling service."""
    
    def __init__(self, ec2):
        self.ec2 = ec2
        self.auto_scaling_groups = {}
    
    def create_auto_scaling_group(self, name, **kwargs):
        """Create auto scaling group."""
        asg = {
            'AutoScalingGroupName': name,
            'MinSize': kwargs.get('MinSize', 1),
            'MaxSize': kwargs.get('MaxSize', 10),
            'DesiredCapacity': kwargs.get('DesiredCapacity', 1),
            'Instances': []
        }
        self.auto_scaling_groups[name] = asg
        logger.info(f"Created auto scaling group: {name}")
        return asg
    
    def set_desired_capacity(self, asg_name, capacity):
        """Set desired capacity for auto scaling group."""
        if asg_name in self.auto_scaling_groups:
            asg = self.auto_scaling_groups[asg_name]
            old_capacity = len(asg['Instances'])
            
            if capacity > old_capacity:
                # Scale up
                diff = capacity - old_capacity
                result = self.ec2.run_instances(MinCount=diff)
                asg['Instances'].extend([i['InstanceId'] for i in result['Instances']])
            elif capacity < old_capacity:
                # Scale down
                diff = old_capacity - capacity
                to_terminate = asg['Instances'][:diff]
                self.ec2.terminate_instances(to_terminate)
                asg['Instances'] = asg['Instances'][diff:]
            
            asg['DesiredCapacity'] = capacity
            logger.info(f"Set {asg_name} capacity to {capacity}")


class MockCloudProvider:
    """Mock cloud provider with Boto3-like interface."""
    
    def __init__(self):
        self.ec2 = MockEC2()
        self.elb = MockELB()
        self.auto_scaling = MockAutoScaling(self.ec2)
        logger.info("Mock cloud provider initialized")
    
    def scale_out(self, count=1):
        """Scale out by adding instances."""
        return self.ec2.run_instances(MinCount=count)
    
    def scale_in(self, instance_ids):
        """Scale in by removing instances."""
        return self.ec2.terminate_instances(instance_ids)
    
    def get_status(self):
        """Get cloud infrastructure status."""
        instances = self.ec2.describe_instances()
        total_instances = sum(len(r['Instances']) for r in instances['Reservations'])
        running_instances = sum(
            1 for r in instances['Reservations'] 
            for i in r['Instances'] 
            if i['State']['Name'] == 'running'
        )
        
        return {
            'total_instances': total_instances,
            'running_instances': running_instances,
            'load_balancers': len(self.elb.load_balancers),
            'auto_scaling_groups': len(self.auto_scaling.auto_scaling_groups)
        }
