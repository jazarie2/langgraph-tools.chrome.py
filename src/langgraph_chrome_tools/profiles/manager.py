"""Chrome profile management for langgraph-chrome-tools.

This module provides comprehensive profile management capabilities including:
- Scratch profiles (temporary, cleaned up automatically)
- No-profile mode (incognito-like, no data persistence)
- Visible UI mode (for profile creation and debugging)
- Persistent profiles with custom names and data directories
"""

import os
import shutil
import tempfile
import uuid
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass

from ..core.exceptions import ProfileError


class ProfileMode(str, Enum):
    """Supported Chrome profile modes.
    
    Attributes:
        SCRATCH: Temporary profile, automatically cleaned up
        NO_PROFILE: No persistent data, similar to incognito mode
        VISIBLE: Visible browser window for debugging and profile creation
        PERSISTENT: Named profile that persists between sessions
    """
    SCRATCH = "scratch"
    NO_PROFILE = "no-profile" 
    VISIBLE = "visible"
    PERSISTENT = "persistent"


@dataclass
class ProfileConfig:
    """Configuration for a Chrome profile.
    
    Attributes:
        mode: Profile mode to use
        name: Profile name (for persistent profiles)
        path: Custom profile directory path
        headless: Whether to run in headless mode
        visible: Whether to show the browser window
        user_data_dir: Base directory for profile data
        args: Additional Chrome arguments
    """
    mode: ProfileMode = ProfileMode.SCRATCH
    name: Optional[str] = None
    path: Optional[Union[str, Path]] = None
    headless: bool = True
    visible: bool = False
    user_data_dir: Optional[Union[str, Path]] = None
    args: Optional[list[str]] = None


class ProfileManager:
    """Manages Chrome profiles for browser automation.
    
    This class handles the creation, management, and cleanup of Chrome profiles
    across different modes (scratch, no-profile, visible, persistent).
    
    Examples:
        >>> # Scratch profile (temporary)
        >>> manager = ProfileManager()
        >>> config = manager.create_profile(ProfileMode.SCRATCH)
        
        >>> # Persistent profile
        >>> config = manager.create_profile(ProfileMode.PERSISTENT, name="my_profile")
        
        >>> # Visible mode for debugging
        >>> config = manager.create_profile(ProfileMode.VISIBLE)
    """
    
    def __init__(
        self,
        base_profile_dir: Optional[Union[str, Path]] = None,
        auto_cleanup: bool = True,
    ) -> None:
        """Initialize the profile manager.
        
        Args:
            base_profile_dir: Base directory for storing profiles
            auto_cleanup: Whether to automatically cleanup scratch profiles
        """
        self.auto_cleanup = auto_cleanup
        self._active_profiles: Dict[str, ProfileConfig] = {}
        self._temp_dirs: list[str] = []
        
        # Set up base profile directory
        if base_profile_dir:
            self.base_profile_dir = Path(base_profile_dir)
        else:
            # Use user's home directory by default
            home_dir = Path.home()
            self.base_profile_dir = home_dir / ".langgraph_chrome_profiles"
        
        # Create base directory if it doesn't exist
        self.base_profile_dir.mkdir(parents=True, exist_ok=True)
    
    def create_profile(
        self,
        mode: ProfileMode = ProfileMode.SCRATCH,
        name: Optional[str] = None,
        visible: bool = False,
        **kwargs: Any,
    ) -> ProfileConfig:
        """Create a new Chrome profile configuration.
        
        Args:
            mode: Profile mode to use
            name: Profile name (required for persistent profiles)
            visible: Whether to show browser window
            **kwargs: Additional configuration options
            
        Returns:
            ProfileConfig: Configuration for the created profile
            
        Raises:
            ProfileError: If profile creation fails
        """
        try:
            if mode == ProfileMode.PERSISTENT and not name:
                raise ProfileError(
                    "Profile name is required for persistent profiles",
                    profile_mode=mode.value,
                )
            
            # Generate unique profile ID
            profile_id = name or f"{mode.value}_{uuid.uuid4().hex[:8]}"
            
            # Create profile configuration based on mode
            if mode == ProfileMode.SCRATCH:
                config = self._create_scratch_profile(profile_id, visible, **kwargs)
            elif mode == ProfileMode.NO_PROFILE:
                config = self._create_no_profile_config(profile_id, visible, **kwargs)
            elif mode == ProfileMode.VISIBLE:
                config = self._create_visible_profile(profile_id, **kwargs)
            elif mode == ProfileMode.PERSISTENT:
                config = self._create_persistent_profile(profile_id, visible, **kwargs)
            else:
                raise ProfileError(f"Unsupported profile mode: {mode}")
            
            # Store active profile
            self._active_profiles[profile_id] = config
            
            return config
            
        except Exception as e:
            raise ProfileError(
                f"Failed to create profile: {e}",
                profile_mode=mode.value,
            ) from e
    
    def _create_scratch_profile(
        self,
        profile_id: str,
        visible: bool = False,
        **kwargs: Any,
    ) -> ProfileConfig:
        """Create a temporary scratch profile."""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=f"chrome_profile_{profile_id}_")
        self._temp_dirs.append(temp_dir)
        
        return ProfileConfig(
            mode=ProfileMode.SCRATCH,
            name=profile_id,
            path=temp_dir,
            headless=not visible,
            visible=visible,
            user_data_dir=temp_dir,
            args=kwargs.get("args", []),
        )
    
    def _create_no_profile_config(
        self,
        profile_id: str,
        visible: bool = False,
        **kwargs: Any,
    ) -> ProfileConfig:
        """Create a no-profile (incognito-like) configuration."""
        args = kwargs.get("args", [])
        args.extend([
            "--incognito",
            "--no-default-browser-check",
            "--no-first-run",
        ])
        
        return ProfileConfig(
            mode=ProfileMode.NO_PROFILE,
            name=profile_id,
            path=None,
            headless=not visible,
            visible=visible,
            user_data_dir=None,
            args=args,
        )
    
    def _create_visible_profile(
        self,
        profile_id: str,
        **kwargs: Any,
    ) -> ProfileConfig:
        """Create a visible profile for debugging and profile creation."""
        # Create persistent directory for visible profiles
        profile_dir = self.base_profile_dir / "visible_profiles" / profile_id
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        args = kwargs.get("args", [])
        args.extend([
            "--no-default-browser-check",
            "--no-first-run",
        ])
        
        return ProfileConfig(
            mode=ProfileMode.VISIBLE,
            name=profile_id,
            path=str(profile_dir),
            headless=False,
            visible=True,
            user_data_dir=str(profile_dir),
            args=args,
        )
    
    def _create_persistent_profile(
        self,
        profile_id: str,
        visible: bool = False,
        **kwargs: Any,
    ) -> ProfileConfig:
        """Create a persistent profile."""
        # Create profile directory
        profile_dir = self.base_profile_dir / "persistent_profiles" / profile_id
        profile_dir.mkdir(parents=True, exist_ok=True)
        
        args = kwargs.get("args", [])
        args.extend([
            "--no-default-browser-check",
            "--no-first-run",
        ])
        
        return ProfileConfig(
            mode=ProfileMode.PERSISTENT,
            name=profile_id,
            path=str(profile_dir),
            headless=not visible,
            visible=visible,
            user_data_dir=str(profile_dir),
            args=args,
        )
    
    def get_profile(self, profile_id: str) -> Optional[ProfileConfig]:
        """Get an existing profile configuration.
        
        Args:
            profile_id: ID of the profile to retrieve
            
        Returns:
            ProfileConfig: Profile configuration if found, None otherwise
        """
        return self._active_profiles.get(profile_id)
    
    def list_profiles(self) -> Dict[str, ProfileConfig]:
        """List all active profiles.
        
        Returns:
            Dict[str, ProfileConfig]: Dictionary of profile ID to configuration
        """
        return self._active_profiles.copy()
    
    def list_persistent_profiles(self) -> list[str]:
        """List all available persistent profiles.
        
        Returns:
            list[str]: List of persistent profile names
        """
        persistent_dir = self.base_profile_dir / "persistent_profiles"
        if not persistent_dir.exists():
            return []
        
        return [
            p.name for p in persistent_dir.iterdir()
            if p.is_dir() and not p.name.startswith('.')
        ]
    
    def delete_profile(self, profile_id: str, force: bool = False) -> bool:
        """Delete a profile and its data.
        
        Args:
            profile_id: ID of the profile to delete
            force: Whether to force deletion even for active profiles
            
        Returns:
            bool: True if profile was deleted, False otherwise
            
        Raises:
            ProfileError: If deletion fails or profile is in use
        """
        try:
            config = self._active_profiles.get(profile_id)
            if not config:
                # Try to find persistent profile
                persistent_dir = self.base_profile_dir / "persistent_profiles" / profile_id
                if persistent_dir.exists():
                    shutil.rmtree(persistent_dir)
                    return True
                return False
            
            # Don't delete if profile is active unless forced
            if not force and config.mode != ProfileMode.SCRATCH:
                raise ProfileError(
                    f"Cannot delete active profile '{profile_id}' without force=True",
                    profile_path=str(config.path) if config.path else None,
                )
            
            # Remove profile data directory
            if config.path and Path(config.path).exists():
                shutil.rmtree(config.path)
            
            # Remove from active profiles
            del self._active_profiles[profile_id]
            
            return True
            
        except Exception as e:
            raise ProfileError(
                f"Failed to delete profile '{profile_id}': {e}",
                profile_path=str(config.path) if config and config.path else None,
            ) from e
    
    def cleanup_scratch_profiles(self) -> int:
        """Clean up all temporary scratch profiles.
        
        Returns:
            int: Number of profiles cleaned up
        """
        cleaned_count = 0
        
        # Clean up temporary directories
        for temp_dir in self._temp_dirs:
            try:
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    cleaned_count += 1
            except Exception:
                # Ignore cleanup errors
                pass
        
        # Clear temp dirs list
        self._temp_dirs.clear()
        
        # Remove scratch profiles from active list
        scratch_profiles = [
            pid for pid, config in self._active_profiles.items()
            if config.mode == ProfileMode.SCRATCH
        ]
        
        for profile_id in scratch_profiles:
            del self._active_profiles[profile_id]
        
        return cleaned_count
    
    def get_browser_args(self, profile_config: ProfileConfig) -> list[str]:
        """Get Chrome browser arguments for a profile configuration.
        
        Args:
            profile_config: Profile configuration
            
        Returns:
            list[str]: List of Chrome command line arguments
        """
        args = []
        
        # Add user data directory if specified
        if profile_config.user_data_dir:
            args.append(f"--user-data-dir={profile_config.user_data_dir}")
        
        # Add profile-specific arguments
        if profile_config.args:
            args.extend(profile_config.args)
        
        # Add common arguments
        args.extend([
            "--disable-blink-features=AutomationControlled",
            "--disable-dev-shm-usage",
            "--disable-extensions",
            "--disable-gpu",
            "--disable-web-security",
            "--no-sandbox",
        ])
        
        return args
    
    def __del__(self) -> None:
        """Cleanup when the profile manager is destroyed."""
        if self.auto_cleanup:
            self.cleanup_scratch_profiles()