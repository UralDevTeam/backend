"""Tests for LDAP client."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import ssl

from src.infrastructure.ldap_client import LdapClient, from_env


class TestLdapClient:
    """Tests for LdapClient."""
    
    def test_init_with_ssl(self):
        """Test initializing client with SSL."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            client = LdapClient(
                host="ldap.example.com",
                port=636,
                use_ssl=True,
                bind_dn="cn=admin,dc=example,dc=com",
                bind_password="password",
                base_dn="dc=example,dc=com"
            )
            
            mock_server.assert_called_once()
            mock_conn.assert_called_once()
    
    def test_init_with_start_tls(self):
        """Test initializing client with STARTTLS."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            mock_conn_instance = MagicMock()
            mock_conn_instance.start_tls.return_value = True
            mock_conn_instance.bind.return_value = True
            mock_conn.return_value = mock_conn_instance
            
            client = LdapClient(
                host="ldap.example.com",
                port=389,
                start_tls=True,
                bind_dn="cn=admin,dc=example,dc=com",
                bind_password="password",
                base_dn="dc=example,dc=com"
            )
            
            mock_conn_instance.start_tls.assert_called_once()
            mock_conn_instance.bind.assert_called_once()
    
    def test_init_start_tls_failure(self):
        """Test that STARTTLS failure raises error."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            mock_conn_instance = MagicMock()
            mock_conn_instance.start_tls.return_value = False
            mock_conn_instance.result = {"description": "TLS negotiation failed"}
            mock_conn.return_value = mock_conn_instance
            
            with pytest.raises(RuntimeError, match="STARTTLS failed"):
                client = LdapClient(
                    host="ldap.example.com",
                    start_tls=True,
                    bind_dn="cn=admin,dc=example,dc=com",
                    bind_password="password"
                )
    
    def test_init_bind_failure(self):
        """Test that bind failure raises error."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            mock_conn_instance = MagicMock()
            mock_conn_instance.start_tls.return_value = True
            mock_conn_instance.bind.return_value = False
            mock_conn_instance.result = {"description": "Invalid credentials"}
            mock_conn.return_value = mock_conn_instance
            
            with pytest.raises(RuntimeError, match="Bind failed"):
                client = LdapClient(
                    host="ldap.example.com",
                    start_tls=True,
                    bind_dn="cn=admin,dc=example,dc=com",
                    bind_password="wrongpassword"
                )
    
    def test_search_success(self):
        """Test successful LDAP search."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            mock_conn_instance = MagicMock()
            mock_conn_instance.bind.return_value = True
            mock_conn_instance.search.return_value = True
            mock_conn_instance.response = [
                {
                    "type": "searchResEntry",
                    "dn": "cn=user1,ou=users,dc=example,dc=com",
                    "attributes": {"cn": "user1", "mail": "user1@example.com"}
                },
                {
                    "type": "searchResEntry",
                    "dn": "cn=user2,ou=users,dc=example,dc=com",
                    "attributes": {"cn": "user2", "mail": "user2@example.com"}
                }
            ]
            mock_conn.return_value = mock_conn_instance
            
            client = LdapClient(
                host="ldap.example.com",
                bind_dn="cn=admin,dc=example,dc=com",
                bind_password="password",
                base_dn="dc=example,dc=com"
            )
            
            results = client.search(
                search_base=None,
                ldap_filter="(objectClass=person)"
            )
            
            assert len(results) == 2
            assert results[0]["dn"] == "cn=user1,ou=users,dc=example,dc=com"
            assert results[1]["dn"] == "cn=user2,ou=users,dc=example,dc=com"
    
    def test_search_failure(self):
        """Test LDAP search failure."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            mock_conn_instance = MagicMock()
            mock_conn_instance.bind.return_value = True
            mock_conn_instance.search.return_value = False
            mock_conn_instance.result = {"description": "Search error"}
            mock_conn.return_value = mock_conn_instance
            
            client = LdapClient(
                host="ldap.example.com",
                bind_dn="cn=admin,dc=example,dc=com",
                bind_password="password"
            )
            
            with pytest.raises(RuntimeError, match="Search error"):
                client.search(search_base="dc=example,dc=com", ldap_filter="(objectClass=*)")
    
    def test_verify_password_success(self):
        """Test password verification success."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            mock_main_conn = MagicMock()
            mock_main_conn.bind.return_value = True
            
            mock_verify_conn = MagicMock()
            mock_verify_conn.bind.return_value = True
            mock_verify_conn.unbind.return_value = None
            
            mock_conn.side_effect = [mock_main_conn, mock_verify_conn]
            
            client = LdapClient(
                host="ldap.example.com",
                bind_dn="cn=admin,dc=example,dc=com",
                bind_password="password"
            )
            
            result = client.verify_password(
                "cn=user1,ou=users,dc=example,dc=com",
                "userpassword"
            )
            
            assert result is True
    
    def test_verify_password_failure(self):
        """Test password verification failure."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            mock_main_conn = MagicMock()
            mock_main_conn.bind.return_value = True
            
            mock_verify_conn = MagicMock()
            mock_verify_conn.bind.return_value = False
            mock_verify_conn.unbind.return_value = None
            
            mock_conn.side_effect = [mock_main_conn, mock_verify_conn]
            
            client = LdapClient(
                host="ldap.example.com",
                bind_dn="cn=admin,dc=example,dc=com",
                bind_password="password"
            )
            
            result = client.verify_password(
                "cn=user1,ou=users,dc=example,dc=com",
                "wrongpassword"
            )
            
            assert result is False
    
    def test_add_entry_success(self):
        """Test adding an entry."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            mock_conn_instance = MagicMock()
            mock_conn_instance.bind.return_value = True
            mock_conn_instance.add.return_value = True
            mock_conn.return_value = mock_conn_instance
            
            client = LdapClient(
                host="ldap.example.com",
                bind_dn="cn=admin,dc=example,dc=com",
                bind_password="password"
            )
            
            client.add_entry(
                "cn=newuser,ou=users,dc=example,dc=com",
                {"cn": "newuser", "objectClass": ["person", "inetOrgPerson"]}
            )
            
            mock_conn_instance.add.assert_called_once()
    
    def test_add_entry_failure(self):
        """Test adding an entry failure."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            mock_conn_instance = MagicMock()
            mock_conn_instance.bind.return_value = True
            mock_conn_instance.add.return_value = False
            mock_conn_instance.result = {"description": "Add failed"}
            mock_conn.return_value = mock_conn_instance
            
            client = LdapClient(
                host="ldap.example.com",
                bind_dn="cn=admin,dc=example,dc=com",
                bind_password="password"
            )
            
            with pytest.raises(RuntimeError, match="Add failed"):
                client.add_entry(
                    "cn=newuser,ou=users,dc=example,dc=com",
                    {"cn": "newuser"}
                )
    
    def test_delete_entry_success(self):
        """Test deleting an entry."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            mock_conn_instance = MagicMock()
            mock_conn_instance.bind.return_value = True
            mock_conn_instance.delete.return_value = True
            mock_conn.return_value = mock_conn_instance
            
            client = LdapClient(
                host="ldap.example.com",
                bind_dn="cn=admin,dc=example,dc=com",
                bind_password="password"
            )
            
            client.delete_entry("cn=user1,ou=users,dc=example,dc=com")
            
            mock_conn_instance.delete.assert_called_once()
    
    def test_close(self):
        """Test closing the connection."""
        with patch('src.infrastructure.ldap_client.Server') as mock_server, \
             patch('src.infrastructure.ldap_client.Connection') as mock_conn:
            
            mock_conn_instance = MagicMock()
            mock_conn_instance.bind.return_value = True
            mock_conn_instance.unbind.return_value = None
            mock_conn.return_value = mock_conn_instance
            
            client = LdapClient(
                host="ldap.example.com",
                bind_dn="cn=admin,dc=example,dc=com",
                bind_password="password"
            )
            
            client.close()
            
            mock_conn_instance.unbind.assert_called_once()


def test_from_env():
    """Test creating LdapClient from environment variables."""
    with patch.dict('os.environ', {
        'LDAP_HOST': 'ldap.test.com',
        'LDAP_PORT': '389',
        'LDAP_SSL': 'false',
        'LDAP_STARTTLS': 'false',
        'LDAP_BIND_DN': 'cn=admin,dc=test,dc=com',
        'LDAP_BIND_PASSWORD': 'testpass',
        'LDAP_BASE_DN': 'dc=test,dc=com',
        'LDAP_TIMEOUT': '10'
    }), \
    patch('src.infrastructure.ldap_client.Server') as mock_server, \
    patch('src.infrastructure.ldap_client.Connection') as mock_conn:
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.bind.return_value = True
        mock_conn.return_value = mock_conn_instance
        
        client = from_env()
        
        assert client.base_dn == 'dc=test,dc=com'
