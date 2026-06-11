import sys

def fix_file(filepath):
    with open(filepath, 'r') as f:
        lines = f.readlines()

    # We want to fix the block from around 148 to 170
    # Specifically the mismatched try/except and elif
    
    new_lines = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Detect the start of the messy block
        if "if self.health_manager is not None:" in line and i > 140:
            # We found line 148
            new_lines.append(line)
            i += 1
            # Skip until we are past the mess, let's say until 'return bars' or similar
            # or just look for line 170.
            # Actually let's reconstruct it carefully.
            new_lines.append("                            try:\n")
            new_lines.append("                                if hasattr(self.health_manager, 'record_degraded'):\n")
            new_lines.append("                                    self.health_manager.record_degraded(self.provider_name, self.pr            new_lines.app=str(e))\n")
             ew_lines.append             e                    elif hasattr(self.health_manager             ew_lines.append             e es.append("                                    self.health_manager.mark_degraded(self.provider_name, self.provider_capability, reason=str(e))\n")
                                                          except Exception:\n")
            new_lines.append("                                pass\n")
            new_lines.append(w handle the pb and evidence_store part if they were there
            new_lines.append("                        # attach provider and evidence markers expected by tests\n")
            new_lines.append("                        try:\n")
            new_lines.append("                            if 'pb' in locals():\n")
            new_lines.append("                                setattr(pb, 'provider', self.provider_name)\n")
            new_lines.append("                        except Exception:\n")
            new_lines.append("                                     new_lines.append("                                     new_lines.append("                                     new_lines.append("                                     new_lines.append("                                     new_lines.append("                           tinue will pick up from i
        else:
            new_lines.append(line)
            i += 1
            
    with open(filepath, 'w') as f:
        f.writelines(new_lines)

if __name__ == "__main__":
    fix_file("trading_os_v1/trading_os_v1/providers/adapters/tiingo.py")
