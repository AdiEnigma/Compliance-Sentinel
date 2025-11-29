"""
Initialize database and memory bank with templates.
"""
import asyncio
import os
from pathlib import Path
from memory.memory_bank import MemoryBank


async def init_memory_bank():
    """Initialize memory bank with templates."""
    memory_bank = MemoryBank()
    
    # Load templates from docs/templates
    template_dir = Path("docs/templates")
    if template_dir.exists():
        for template_file in template_dir.glob("*.txt"):
            template_id = template_file.stem
            with open(template_file, "r", encoding="utf-8") as f:
                template_text = f.read()
            
            await memory_bank.store_template(template_id, template_text)
            print(f"Loaded template: {template_id}")
    
    # Save memory bank
    memory_bank.save()
    print("Memory bank initialized")


if __name__ == "__main__":
    asyncio.run(init_memory_bank())

