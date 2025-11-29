"""
Audit trail service for storing and retrieving document processing history.
"""
import os
import json
import zipfile
import shutil
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AuditTrailService:
    """Manages audit trails for document processing."""
    
    def __init__(self, audit_dir: str = "./data/audit_trails"):
        self.audit_dir = audit_dir
        os.makedirs(audit_dir, exist_ok=True)
    
    async def save_audit_trail(
        self,
        processing_id: str,
        original_file: str,
        result: Dict[str, Any],
        parsed_document: Dict[str, Any]
    ):
        """Save complete audit trail for a processed document."""
        audit_path = os.path.join(self.audit_dir, processing_id)
        os.makedirs(audit_path, exist_ok=True)
        
        # Save original file
        if os.path.exists(original_file):
            shutil.copy2(original_file, os.path.join(audit_path, "original" + Path(original_file).suffix))
        
        # Save agent outputs
        agent_outputs = result.get("agent_outputs", {})
        with open(os.path.join(audit_path, "agent_outputs.json"), "w") as f:
            json.dump(agent_outputs, f, indent=2)
        
        # Save result summary
        with open(os.path.join(audit_path, "result.json"), "w") as f:
            json.dump(result, f, indent=2)
        
        # Save parsed document
        with open(os.path.join(audit_path, "parsed_document.json"), "w") as f:
            json.dump(parsed_document, f, indent=2, default=str)
        
        # Generate diff if suggestions exist
        if result.get("suggestions"):
            await self._generate_diff(audit_path, parsed_document["full_text"], result["suggestions"])
        
        # Create final document if auto-fix was applied
        if result.get("approval_decision") == "Auto-Fix":
            final_text = await self._apply_fixes(parsed_document["full_text"], result["suggestions"])
            with open(os.path.join(audit_path, "final_document.txt"), "w", encoding="utf-8") as f:
                f.write(final_text)
        
        logger.info(f"Audit trail saved for {processing_id}")
    
    async def _generate_diff(self, audit_path: str, original_text: str, suggestions: list):
        """Generate diff showing suggested changes."""
        try:
            from diff_match_patch import diff_match_patch
        except ImportError:
            # Fallback if diff_match_patch not available
            logger.warning("diff_match_patch not available, skipping diff generation")
            return
        
        dmp = diff_match_patch()
        modified_text = original_text
        
        # Apply suggestions in reverse order to maintain indices
        sorted_suggestions = sorted(suggestions, key=lambda x: x.get("span_start", 0), reverse=True)
        
        for suggestion in sorted_suggestions:
            start = suggestion.get("span_start", 0)
            end = suggestion.get("span_end", 0)
            replacement = suggestion.get("replacement", "")
            modified_text = modified_text[:start] + replacement + modified_text[end:]
        
        # Generate diff
        diffs = dmp.diff_main(original_text, modified_text)
        dmp.diff_cleanupSemantic(diffs)
        diff_text = dmp.diff_prettyHtml(diffs)
        
        with open(os.path.join(audit_path, "diff.html"), "w", encoding="utf-8") as f:
            f.write(f"<html><body>{diff_text}</body></html>")
    
    async def _apply_fixes(self, original_text: str, suggestions: list) -> str:
        """Apply fixes to text."""
        modified_text = original_text
        sorted_suggestions = sorted(suggestions, key=lambda x: x.get("span_start", 0), reverse=True)
        
        for suggestion in sorted_suggestions:
            start = suggestion.get("span_start", 0)
            end = suggestion.get("span_end", 0)
            replacement = suggestion.get("replacement", "")
            modified_text = modified_text[:start] + replacement + modified_text[end:]
        
        return modified_text
    
    async def get_audit_bundle_path(self, processing_id: str) -> Optional[str]:
        """Create and return path to audit trail bundle ZIP."""
        audit_path = os.path.join(self.audit_dir, processing_id)
        if not os.path.exists(audit_path):
            return None
        
        bundle_path = os.path.join(self.audit_dir, f"{processing_id}_bundle.zip")
        
        with zipfile.ZipFile(bundle_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(audit_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, audit_path)
                    zipf.write(file_path, arcname)
        
        return bundle_path

