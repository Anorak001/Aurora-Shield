#!/usr/bin/env python3
"""
Aurora Shield - Main Entry Point
Launch the complete DDoS protection system with dashboard.
"""

import sys
import logging
from aurora_shield.shield_manager import AuroraShieldManager
from aurora_shield.dashboard.web_dashboard import WebDashboard
from aurora_shield.config import DEFAULT_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """Main entry point for Aurora Shield."""
    logger.info("=" * 60)
    logger.info("🛡️  Aurora Shield - DDoS Protection Framework")
    logger.info("=" * 60)
    
    try:
        # Initialize Aurora Shield with default configuration
        logger.info("Initializing Aurora Shield Manager...")
        shield_manager = AuroraShieldManager(DEFAULT_CONFIG)
        
        # Create and launch web dashboard
        logger.info("Starting Web Dashboard...")
        dashboard = WebDashboard(shield_manager)
        
        host = DEFAULT_CONFIG['dashboard']['host']
        port = DEFAULT_CONFIG['dashboard']['port']
        
        logger.info(f"✅ Aurora Shield is ready!")
        logger.info(f"📊 Dashboard: http://localhost:{port}")
        logger.info(f"🔍 API Stats: http://localhost:{port}/api/dashboard/stats")
        logger.info("")
        logger.info("Press Ctrl+C to stop")
        logger.info("=" * 60)
        
        # Run the dashboard (blocking)
        dashboard.run(host=host, port=port, debug=False)
        
    except KeyboardInterrupt:
        logger.info("\n\n👋 Shutting down Aurora Shield...")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
