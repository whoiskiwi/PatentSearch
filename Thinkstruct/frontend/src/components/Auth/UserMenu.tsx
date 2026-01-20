/**
 * User Menu Component - Shows user info and logout option
 */

import { useState, useRef, useEffect } from 'react';
import { useAuth } from '../../auth';

interface UserMenuProps {
  className?: string;
}

export function UserMenu({ className = '' }: UserMenuProps) {
  const { user, logout, isLoading } = useAuth();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menu when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  if (isLoading || !user) {
    return null;
  }

  const handleLogout = async () => {
    setIsOpen(false);
    await logout();
  };

  const initials = user.name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  return (
    <div className={`user-menu ${className}`} ref={menuRef}>
      <button
        className="user-menu-trigger"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="true"
      >
        {user.picture_url ? (
          <img
            src={user.picture_url}
            alt={user.name}
            className="user-avatar"
          />
        ) : (
          <div className="user-avatar-placeholder">{initials}</div>
        )}
        <span className="user-name">{user.name}</span>
        <svg
          className={`dropdown-arrow ${isOpen ? 'open' : ''}`}
          width="12"
          height="12"
          viewBox="0 0 12 12"
        >
          <path
            d="M2.5 4.5l3.5 3.5 3.5-3.5"
            stroke="currentColor"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            fill="none"
          />
        </svg>
      </button>

      {isOpen && (
        <div className="user-menu-dropdown">
          <div className="user-menu-header">
            {user.picture_url ? (
              <img
                src={user.picture_url}
                alt={user.name}
                className="user-avatar-large"
              />
            ) : (
              <div className="user-avatar-large-placeholder">{initials}</div>
            )}
            <div className="user-info">
              <div className="user-name-full">{user.name}</div>
              <div className="user-email">{user.email}</div>
            </div>
          </div>
          <div className="user-menu-divider"></div>
          <button className="user-menu-item logout" onClick={handleLogout}>
            <svg width="16" height="16" viewBox="0 0 16 16">
              <path
                fill="currentColor"
                d="M11 3v2h-1V3H3v10h7v-2h1v2a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1h7a1 1 0 011 1z"
              />
              <path
                fill="currentColor"
                d="M13.85 8l-2.15 2.15.7.7L15.25 8 12.4 5.15l-.7.7L13.85 8z"
              />
              <path fill="currentColor" d="M6 7h7v1H6z" />
            </svg>
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}

export default UserMenu;
