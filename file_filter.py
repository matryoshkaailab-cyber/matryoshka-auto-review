"""
File Filter Module for MATRYOSHKA Auto-Review

Filters out binary and asset files from PR diff.
Only actual code files are sent to AI for review.
"""

from typing import List, Dict, Any


class FileFilter:
    """
    Фильтр файлов для код-ревью.
    
    Игнорирует:
    - Бинарные файлы (.dll, .so, .exe, .bin)
    - Ассеты (.png, .jpg, .gif, .mp3, .wav)
    - Мета-файлы (.meta, .gitignore, .DS_Store)
    - Скомпилированные файлы (.pyc, .class, .o)
    - Lock файлы (package-lock.json, requirements.lock)
    """
    
    # Расширения для ревью (только код)
    REVIEW_EXTENSIONS = {
        # Web
        '.py', '.js', '.ts', '.jsx', '.tsx', '.vue', '.svelte',
        '.html', '.css', '.scss', '.sass', '.less',
        
        # Backend
        '.cs', '.java', '.kt', '.scala', '.go', '.rs', '.php',
        '.rb', '.swift', '.m', '.mm',
        
        # Config & Data
        '.json', '.xml', '.yaml', '.yml', '.toml', '.ini', '.cfg',
        '.md', '.txt', '.rst', '.adoc',
        
        # Shell & Scripts
        '.sh', '.bash', '.zsh', '.fish', '.ps1', '.bat', '.cmd',
        '.gradle', '.make', '.cmake',
        
        # Database
        '.sql', '.graphql',
        
        # Infrastructure
        '.tf', '.hcl', '.dockerfile', '.env.example',
    }
    
    # Игнорируемые расширения (бинарные и ассеты)
    IGNORE_EXTENSIONS = {
        # Binary
        '.dll', '.so', '.exe', '.bin', '.dat', '.db', '.sqlite',
        
        # Images
        '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.svg', '.ico',
        '.webp', '.tiff', '.psd', '.ai',
        
        # Audio/Video
        '.mp3', '.wav', '.ogg', '.flac', '.mp4', '.avi', '.mov',
        '.mkv', '.webm',
        
        # Unity/Game assets
        '.meta', '.prefab', '.unity', '.asset', '.mat', '.fbx',
        '.obj', '.blend', '.shader', '.anim', '.controller',
        
        # Compiled
        '.pyc', '.pyo', '.class', '.o', '.obj', '.a', '.lib',
        '.jar', '.war', '.ear',
        
        # Archives
        '.zip', '.tar', '.gz', '.rar', '.7z',
        
        # IDE & System
        '.gitignore', '.gitattributes', '.DS_Store', '.idea',
        '.vscode', '.env', '.env.local',
        
        # Lock files (слишком большие)
        '.lock',
    }
    
    # Игнорируемые пути (папки)
    IGNORE_PATHS = {
        'node_modules',
        'vendor',
        '__pycache__',
        '.git',
        '.svn',
        'dist',
        'build',
        'coverage',
        '.next',
        '.nuxt',
        'venv',
        '.venv',
        'env',
        '.env',
    }
    
    def __init__(self, custom_ignore: List[str] = None, custom_review: List[str] = None):
        """
        Инициализация фильтра.
        
        Args:
            custom_ignore: Дополнительные расширения для игнорирования
            custom_review: Дополнительные расширения для ревью
        """
        if custom_ignore:
            self.IGNORE_EXTENSIONS.update(ext.lower() for ext in custom_ignore)
        if custom_review:
            self.REVIEW_EXTENSIONS.update(ext.lower() for ext in custom_review)
    
    def should_review(self, file_path: str) -> bool:
        """
        Проверить, нужно ли ревьювить файл.
        
        Args:
            file_path: Путь к файлу (например, 'src/main.py')
            
        Returns:
            True если файл нужно ревьювить
        """
        # Нормализуем путь
        file_path = file_path.replace('\\', '/').lower()
        
        # Проверка папок
        path_parts = file_path.split('/')
        for part in path_parts:
            if part in self.IGNORE_PATHS:
                return False
        
        # Проверка расширений
        ext = self._get_extension(file_path)
        
        if not ext:
            # Нет расширения — проверяем имя
            filename = file_path.split('/')[-1]
            if filename in {'Dockerfile', 'Makefile', 'LICENSE', 'README'}:
                return True
            return False
        
        if ext in self.IGNORE_EXTENSIONS:
            return False
        
        if ext in self.REVIEW_EXTENSIONS:
            return True
        
        # По умолчанию игнорируем неизвестные расширения
        return False
    
    def _get_extension(self, file_path: str) -> str:
        """
        Получить расширение файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Расширение в нижнем регистре (например, '.py')
        """
        filename = file_path.split('/')[-1]
        if '.' in filename:
            return '.' + filename.rsplit('.', 1)[1].lower()
        return ''
    
    def filter_files(self, files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Отфильтровать список файлов.
        
        Args:
            files: Список файлов из GitHub API
            
        Returns:
            Отфильтрованный список (только код для ревью)
        """
        return [f for f in files if self.should_review(f.get('filename', ''))]
    
    def filter_diff(self, diff_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Отфильтровать diff PR.
        
        Args:
            diff_files: Файлы из get_pr_diff
            
        Returns:
            Словарь с отфильтрованными файлами и статистикой
        """
        filtered = []
        skipped_count = 0
        
        for file in diff_files:
            if self.should_review(file.get('filename', '')):
                filtered.append(file)
            else:
                skipped_count += 1
        
        return {
            'files': filtered,
            'total_files': len(diff_files),
            'reviewed_files': len(filtered),
            'skipped_files': skipped_count,
        }
