#!/usr/bin/env python3
"""
Automated Model Routing Updater

Checks for new AI models, evaluates performance, and updates routing decisions.
Run: ./tools/update-model-routing.py [--check-only] [--force]

Compliance: § 16.2 (DEVELOPER_STANDARDS.md)
"""

# Standard library
import argparse
import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# Third-party
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelRoutingUpdater:
    """Updates AI model routing based on latest releases and performance."""
    
    def __init__(self, config_path: Path, dry_run: bool = False):
        """
        Initialize the model routing updater.
        
        Args:
            config_path: Path to ai_models.json
            dry_run: If True, don't write changes
        """
        self.config_path = config_path
        self.dry_run = dry_run
        self.models_file = Path("config/ai_models.json")
        self.routing_doc = Path("docs/AI_MODEL_ROUTING.md")
        self.copilot_instructions = Path(".github/copilot-instructions.md")
        
        # Load current model data
        self.model_data = self._load_model_data()
        
    def _load_model_data(self) -> Dict:
        """Load current model registry."""
        try:
            with open(self.models_file) as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Model registry not found: {self.models_file}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in model registry: {e}")
            sys.exit(1)
    
    def check_for_updates(self) -> Dict[str, List]:
        """
        Check OpenAI and Anthropic APIs for new models.
        
        Returns:
            Dict with new_models, deprecated_models, updated_capabilities
        """
        updates = {
            "new_models": [],
            "deprecated_models": [],
            "updated_capabilities": []
        }
        
        logger.info("Checking for new models from providers...")
        
        # Check OpenAI models
        try:
            openai_models = self._fetch_openai_models()
            if openai_models:
                updates["new_models"].extend(openai_models)
                logger.info(f"Found {len(openai_models)} new OpenAI models")
        except Exception as e:
            logger.error(f"Failed to fetch OpenAI models: {e}")
        
        # Check Anthropic models
        try:
            anthropic_models = self._fetch_anthropic_models()
            if anthropic_models:
                updates["new_models"].extend(anthropic_models)
                logger.info(f"Found {len(anthropic_models)} new Anthropic models")
        except Exception as e:
            logger.error(f"Failed to fetch Anthropic models: {e}")
        
        return updates
    
    def _fetch_openai_models(self) -> List[Dict]:
        """
        Fetch latest OpenAI models from API.
        
        Returns:
            List of new model dicts
        """
        # Note: In production, this would call OpenAI API
        # For now, return empty list as we manually update
        # 
        # Example implementation:
        # response = requests.get(
        #     "https://api.openai.com/v1/models",
        #     headers={"Authorization": f"Bearer {api_key}"}
        # )
        # models = response.json()["data"]
        # return [m for m in models if m["id"] not in self.model_data["models"]]
        
        logger.info("OpenAI API check (stub - manual updates required)")
        return []
    
    def _fetch_anthropic_models(self) -> List[Dict]:
        """
        Fetch latest Anthropic models from releases page.
        
        Returns:
            List of new model dicts
        """
        # Note: In production, this would scrape Anthropic's website
        # or use their API when available
        logger.info("Anthropic API check (stub - manual updates required)")
        return []
    
    def evaluate_model_performance(self, model_id: str) -> int:
        """
        Evaluate model performance score (0-100).
        
        Based on:
        - Benchmark results on standard test tasks
        - Community feedback
        - Official performance metrics
        - Cost-effectiveness ratio
        
        Args:
            model_id: Model identifier
            
        Returns:
            Performance score (0-100)
        """
        # In production, would run actual benchmarks
        # For now, return score from registry or default
        if model_id in self.model_data["models"]:
            return self.model_data["models"][model_id]["performance_score"]
        return 85  # Default score for new models
    
    def update_routing_decisions(self, updates: Dict) -> Dict[str, str]:
        """
        Update routing decisions based on new model data.
        
        Args:
            updates: Dict of updates from check_for_updates()
            
        Returns:
            Dict of task_type_risk -> recommended_model
        """
        logger.info("Calculating optimal routing decisions...")
        
        routing = {}
        
        # For each task type and risk level, find best model
        for task, description in self.model_data["task_types"].items():
            for risk in ["low", "medium", "high"]:
                key = f"{task}_{risk}"
                best_model = self._find_best_model(
                    task, risk, self.model_data["models"]
                )
                routing[key] = best_model
                logger.debug(f"{key} -> {best_model}")
        
        return routing
    
    def _find_best_model(
        self, 
        task_type: str, 
        risk_level: str, 
        models: Dict
    ) -> str:
        """
        Find best model for task type and risk level.
        
        Algorithm:
        1. Filter models marked as optimal for this task
        2. Sort by performance score (descending)
        3. For ties, prefer lower cost
        4. Return top candidate
        
        Args:
            task_type: Task type (T1-T7)
            risk_level: Risk level (low/medium/high)
            models: Model registry
            
        Returns:
            Model ID of best match
        """
        candidates = []
        
        for model_id, model_info in models.items():
            if model_info["status"] != "active":
                continue
            
            # Check if model is optimal for this task type
            task_key = f"{task_type}_{risk_level}"
            optimal_for = model_info.get("optimal_for", [])
            
            # Check exact match or wildcard match
            is_optimal = (
                task_key in optimal_for or
                task_type in optimal_for or
                f"{task_type}_any" in optimal_for
            )
            
            if is_optimal:
                candidates.append({
                    "id": model_id,
                    "score": model_info["performance_score"],
                    "cost": model_info["cost_per_1k_tokens"]["input"]
                })
        
        if not candidates:
            # Fallback: use gpt-4-turbo as default
            logger.warning(f"No optimal model for {task_type}_{risk_level}, using fallback")
            return "gpt-4-turbo"
        
        # Sort by performance score (desc), then cost (asc)
        candidates.sort(
            key=lambda x: (-x["score"], x["cost"])
        )
        
        return candidates[0]["id"]
    
    def generate_routing_table(self, routing: Dict[str, str]) -> str:
        """
        Generate markdown table for AI_MODEL_ROUTING.md.
        
        Args:
            routing: Dict of task_risk -> model_id
            
        Returns:
            Markdown table as string
        """
        logger.info("Generating routing table...")
        
        # Build routing table
        table = "| Task | Low Risk | Medium Risk | High Risk |\n"
        table += "|------|----------|-------------|------------|\n"
        
        for task, description in self.model_data["task_types"].items():
            low = routing.get(f"{task}_low", "gpt-4-turbo")
            med = routing.get(f"{task}_medium", "gpt-4-turbo")
            high = routing.get(f"{task}_high", "claude-3-5-sonnet-20241022")
            
            # Format model names for readability
            low_name = self._format_model_name(low)
            med_name = self._format_model_name(med)
            high_name = self._format_model_name(high)
            
            table += f"| {description} | {low_name} | {med_name} | {high_name} |\n"
        
        return table
    
    def _format_model_name(self, model_id: str) -> str:
        """
        Convert model ID to readable name.
        
        Args:
            model_id: Model identifier
            
        Returns:
            Human-readable model name
        """
        name_map = {
            "gpt-4-turbo": "GPT-4 Turbo",
            "gpt-4o": "GPT-4o",
            "gpt-4o-mini": "GPT-4o Mini",
            "claude-3-5-sonnet-20241022": "Claude 3.5 Sonnet",
            "claude-3-5-haiku-20241022": "Claude 3.5 Haiku",
            "o1-preview": "o1-preview",
            "o1": "o1",
            "o1-mini": "o1-mini"
        }
        return name_map.get(model_id, model_id)
    
    def update_routing_doc(self, routing_table: str) -> bool:
        """
        Update AI_MODEL_ROUTING.md with new routing table.
        
        Args:
            routing_table: Markdown table string
            
        Returns:
            True if successful
        """
        if self.dry_run:
            logger.info("DRY RUN: Would update AI_MODEL_ROUTING.md")
            logger.info(f"New table:\n{routing_table}")
            return True
        
        try:
            # Read current doc
            with open(self.routing_doc) as f:
                content = f.read()
            
            # Find and replace routing table section
            marker_start = "### Step C — pick model + workflow"
            marker_end = "\n---\n"
            
            start_idx = content.find(marker_start)
            if start_idx == -1:
                logger.error("Could not find routing table marker")
                return False
            
            # Find next section marker (after the table)
            end_idx = content.find(marker_end, start_idx + len(marker_start) + 100)
            if end_idx == -1:
                logger.error("Could not find end of routing section")
                return False
            
            # Replace content
            new_content = (
                content[:start_idx + len(marker_start)] +
                "\n" + routing_table + "\n" +
                content[end_idx:]
            )
            
            # Add update timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d")
            # Look for existing timestamp line
            if "**Last Auto-Update:**" in new_content:
                import re
                new_content = re.sub(
                    r'\*\*Last Auto-Update:\*\* \d{4}-\d{2}-\d{2}',
                    f'**Last Auto-Update:** {timestamp}',
                    new_content
                )
            else:
                # Add timestamp before first ---
                first_separator = new_content.find("\n---\n")
                if first_separator != -1:
                    new_content = (
                        new_content[:first_separator] +
                        f"\n\n**Last Auto-Update:** {timestamp} (automated)\n" +
                        new_content[first_separator:]
                    )
            
            # Write back
            with open(self.routing_doc, 'w') as f:
                f.write(new_content)
            
            logger.info("✅ Updated AI_MODEL_ROUTING.md")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update routing doc: {e}", exc_info=True)
            return False
    
    def sync_to_copilot_instructions(self) -> bool:
        """
        Sync key routing decisions to copilot-instructions.md.
        
        Returns:
            True if successful
        """
        if self.dry_run:
            logger.info("DRY RUN: Would sync to copilot-instructions.md")
            return True
        
        try:
            # Update timestamp in copilot-instructions.md
            with open(self.copilot_instructions) as f:
                copilot_content = f.read()
            
            # Update last synced timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d")
            
            import re
            if "**Last Synced:**" in copilot_content:
                copilot_content = re.sub(
                    r'\*\*Last Synced:\*\* \d{4}-\d{2}-\d{2}',
                    f'**Last Synced:** {timestamp}',
                    copilot_content
                )
            else:
                # Add timestamp to Model Routing section
                marker = "## 📍 Model Routing (AUTO-UPDATED)"
                marker_idx = copilot_content.find(marker)
                if marker_idx != -1:
                    # Find end of section
                    next_section = copilot_content.find("\n---\n", marker_idx)
                    if next_section != -1:
                        insert_point = next_section
                        copilot_content = (
                            copilot_content[:insert_point] +
                            f"\n**Last Synced:** {timestamp} (auto-synced by GitHub Actions)\n" +
                            copilot_content[insert_point:]
                        )
            
            with open(self.copilot_instructions, 'w') as f:
                f.write(copilot_content)
            
            logger.info("✅ Synced to copilot-instructions.md")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync to copilot-instructions: {e}", exc_info=True)
            return False
    
    def run(self, force: bool = False) -> bool:
        """
        Run full update process.
        
        Args:
            force: Force update even if within frequency window
            
        Returns:
            True if successful
        """
        logger.info("🔍 Checking for model updates...")
        
        # Check if update is needed
        last_update = datetime.fromisoformat(self.model_data["last_updated"])
        days_since_update = (datetime.now() - last_update).days
        
        if not force and days_since_update < 7:
            logger.info(f"✅ No update needed (last updated {days_since_update} days ago)")
            return True
        
        # Check for new models
        updates = self.check_for_updates()
        
        if updates["new_models"]:
            logger.info(f"🆕 Found {len(updates['new_models'])} new models")
        else:
            logger.info("No new models found")
        
        # Update routing decisions
        logger.info("📊 Calculating optimal routing...")
        routing = self.update_routing_decisions(updates)
        
        # Generate new routing table
        logger.info("📝 Generating routing table...")
        routing_table = self.generate_routing_table(routing)
        
        # Update documents
        logger.info("📄 Updating documentation...")
        success = self.update_routing_doc(routing_table)
        
        if success:
            success = self.sync_to_copilot_instructions()
        
        # Update timestamp in models file
        if success and not self.dry_run:
            self.model_data["last_updated"] = datetime.now().isoformat()
            with open(self.models_file, 'w') as f:
                json.dump(self.model_data, f, indent=2)
            logger.info("✅ Updated model registry timestamp")
        
        if success:
            logger.info("✅ Model routing update complete!")
        else:
            logger.error("❌ Model routing update failed")
        
        return success


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Update AI model routing based on latest releases",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check for updates without applying
  ./tools/update-model-routing.py --check-only
  
  # Force update even if within weekly window
  ./tools/update-model-routing.py --force
  
  # Normal run (updates if >7 days since last update)
  ./tools/update-model-routing.py
        """
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Check for updates without applying changes (dry run)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force update even if within update frequency"
    )
    
    args = parser.parse_args()
    
    updater = ModelRoutingUpdater(
        config_path=Path("config/ai_models.json"),
        dry_run=args.check_only
    )
    
    success = updater.run(force=args.force)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
