#!/usr/bin/env python3

import os
import base64
from cryptography.fernet import Fernet
from pathlib import Path
from typing import Optional

def generate_encryption_key(env_path: Optional[Path] = None) -> str:
    """Generate a new Fernet encryption key and save it to .env file."""
    
    # Generate new Fernet key
    key = Fernet.generate_key()
    key_str = key.decode()  # Convert bytes to string for storage
    
    # Default to current directory if no path provided
    env_path = env_path or Path('.env')
    
    # Read existing .env content
    env_content = {}
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    try:
                        key_value = line.split('=', 1)
                        if len(key_value) == 2:
                            env_content[key_value[0]] = key_value[1]
                    except Exception as e:
                        print(f"Warning: Skipping malformed line: {line}")
    
    # Update or add the encryption key
    env_content['ENCRYPTION_KEY'] = key_str
    
    # Write back to .env file
    with open(env_path, 'w') as f:
        for k, v in env_content.items():
            f.write(f'{k}={v}\n')
    
    # Verify the key is valid
    try:
        Fernet(key)
        print("✅ Key validation successful")
    except Exception as e:
        print(f"❌ Key validation failed: {e}")
        raise
    
    return key_str

def main():
    """Main function to generate key and handle the process."""
    try:
        # Generate and save the key
        key = generate_encryption_key()
        
        print("\nEncryption key generated successfully! 🔐")
        print("\nKey details:")
        print("------------")
        print(f"Key: {key}")
        print("\nThe key has been saved to your .env file.")
        
    except Exception as e:
        print(f"\n❌ Error generating encryption key: {str(e)}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())