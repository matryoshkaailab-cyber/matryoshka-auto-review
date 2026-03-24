"""
GitHub Client Module for MATRYOSHKA Auto-Review

Handles GitHub API authentication and operations.
"""

import os
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin


class GitHubClient:
    """
    Клиент для работы с GitHub API.
    
    Поддерживает:
    - Аутентификация через токен
    - Получение списка PR
    - Получение diff PR
    - Создание комментариев
    - Создание review
    """
    
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, repo: str):
        """
        Инициализация клиента.
        
        Args:
            token: GitHub Personal Access Token (ghp_...)
            repo: Репозиторий в формате 'owner/repo'
        """
        self.token = token
        self.repo = repo
        
        # Парсим owner/repo
        parts = repo.split('/')
        if len(parts) != 2:
            raise ValueError(f"Invalid repo format: {repo}. Expected 'owner/repo'")
        
        self.owner = parts[0]
        self.repo_name = parts[1]
        
        # Сессия для переиспользования соединения
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'MATRYOSHKA-Auto-Review/1.0'
        })
    
    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        GET запрос к GitHub API.
        
        Args:
            endpoint: Endpoint path (например, '/repos/owner/repo/pulls')
            params: Query parameters
            
        Returns:
            JSON response
        """
        url = urljoin(self.BASE_URL, endpoint)
        response = self.session.get(url, params=params)
        response.raise_for_status()
        return response.json()
    
    def _post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        POST запрос к GitHub API.
        
        Args:
            endpoint: Endpoint path
            data: JSON body
            
        Returns:
            JSON response
        """
        url = urljoin(self.BASE_URL, endpoint)
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def _put(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        PUT запрос к GitHub API.
        """
        url = urljoin(self.BASE_URL, endpoint)
        response = self.session.put(url, json=data)
        response.raise_for_status()
        return response.json()
    
    # ==================== PULL REQUESTS ====================
    
    def list_open_prs(self, state: str = 'open', sort: str = 'created', 
                      direction: str = 'desc', per_page: int = 30) -> List[Dict[str, Any]]:
        """
        Получить список открытых PR.
        
        Args:
            state: Состояние PR ('open', 'closed', 'all')
            sort: Сортировка ('created', 'updated', 'popularity', 'long-running')
            direction: Направление ('asc', 'desc')
            per_page: Количество результатов на страницу
            
        Returns:
            Список PR
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls"
        params = {
            'state': state,
            'sort': sort,
            'direction': direction,
            'per_page': min(per_page, 100)  # GitHub limit
        }
        return self._get(endpoint, params)
    
    def get_pr(self, pr_number: int) -> Dict[str, Any]:
        """
        Получить информацию о PR.
        
        Args:
            pr_number: Номер PR
            
        Returns:
            Информация о PR
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls/{pr_number}"
        return self._get(endpoint)
    
    def get_pr_diff(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        Получить diff PR (список файлов с изменениями).
        
        Args:
            pr_number: Номер PR
            
        Returns:
            Список файлов с изменениями
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls/{pr_number}/files"
        params = {'per_page': 100}
        return self._get(endpoint, params)
    
    def get_pr_commits(self, pr_number: int) -> List[Dict[str, Any]]:
        """
        Получить коммиты PR.
        
        Args:
            pr_number: Номер PR
            
        Returns:
            Список коммитов
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls/{pr_number}/commits"
        params = {'per_page': 100}
        return self._get(endpoint, params)
    
    # ==================== COMMENTS & REVIEWS ====================
    
    def create_comment(self, pr_number: int, body: str, 
                       path: Optional[str] = None, 
                       position: Optional[int] = None,
                       commit_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Создать комментарий к PR.
        
        Args:
            pr_number: Номер PR
            body: Текст комментария
            path: Путь к файлу (для inline комментария)
            position: Позиция в diff (для inline комментария)
            commit_id: SHA коммита
            
        Returns:
            Созданный комментарий
        """
        if path and position:
            # Inline комментарий к файлу
            endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls/{pr_number}/comments"
            data = {
                'body': body,
                'path': path,
                'position': position,
            }
            if commit_id:
                data['commit_id'] = commit_id
        else:
            # Общий комментарий к PR
            endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls/{pr_number}/comments"
            data = {'body': body}
        
        return self._post(endpoint, data)
    
    def create_review(self, pr_number: int, body: str, 
                      event: str = 'COMMENT',
                      commit_id: Optional[str] = None,
                      comments: Optional[List[Dict]] = None) -> Dict[str, Any]:
        """
        Создать review PR.
        
        Args:
            pr_number: Номер PR
            body: Текст review
            event: Тип события ('APPROVE', 'REQUEST_CHANGES', 'COMMENT')
            commit_id: SHA коммита
            comments: Список inline комментариев
            
        Returns:
            Созданный review
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}/pulls/{pr_number}/reviews"
        data = {
            'body': body,
            'event': event,
        }
        if commit_id:
            data['commit_id'] = commit_id
        if comments:
            data['comments'] = comments
        
        return self._post(endpoint, data)
    
    # ==================== FILES & CONTENT ====================
    
    def get_file_content(self, path: str, ref: str = 'main') -> Dict[str, Any]:
        """
        Получить содержимое файла.
        
        Args:
            path: Путь к файлу в репозитории
            ref: Ветка или SHA коммита
            
        Returns:
            Содержимое файла (base64)
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}/contents/{path}"
        params = {'ref': ref}
        return self._get(endpoint, params)
    
    # ==================== UTILITIES ====================
    
    def test_connection(self) -> bool:
        """
        Проверить соединение с GitHub API.
        
        Returns:
            True если соединение успешно
        """
        try:
            endpoint = f"/repos/{self.owner}/{self.repo_name}"
            self._get(endpoint)
            return True
        except Exception:
            return False
    
    def get_repo_info(self) -> Dict[str, Any]:
        """
        Получить информацию о репозитории.
        
        Returns:
            Информация о репозитории
        """
        endpoint = f"/repos/{self.owner}/{self.repo_name}"
        return self._get(endpoint)
