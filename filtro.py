import os
import tkinter as tk
from tkinter import filedialog
from termcolor import colored
from concurrent.futures import ProcessPoolExecutor, as_completed
import re

os.system('cls' if os.name == 'nt' else 'clear')

banner = """
███╗   ██╗ ██╗██╗  ██╗██╗  ██╗██╗  ██╗██╗  ██╗██╗  ██╗
████╗  ██║███║╚██╗██╔╝██║ ██╔╝██║ ██╔╝██║ ██╔╝██║ ██╔╝
██╔██╗ ██║╚██║ ╚███╔╝ █████╔╝ █████╔╝ █████╔╝ █████╔╝ 
██║╚██╗██║ ██║ ██╔██╗ ██╔═██╗ ██╔═██╗ ██╔═██╗ ██╔═██╗ 
██║ ╚████║ ██║██╔╝ ██╗██║  ██╗██║  ██╗██║  ██╗██║  ██╗
╚═╝  ╚═══╝ ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝

      🔍 SEARCH & EXTRACT TOOL By: https://t.me/N1XKKKK 🔍
"""

def scan_file(file_path, keyword):
    found_lines = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                if keyword.lower() in line.lower():
                    found_lines.append(f"[{os.path.basename(file_path)}:{line_num}] {line.strip()}")
    except UnicodeDecodeError:
        try:
            with open(file_path, 'r', encoding='ISO-8859-1') as file:
                for line_num, line in enumerate(file, 1):
                    if keyword.lower() in line.lower():
                        found_lines.append(f"[{os.path.basename(file_path)}:{line_num}] {line.strip()}")
        except Exception as e:
            print(f"Erro ao ler o arquivo {file_path}: {e}")
    return found_lines

def scan_files(directory, keyword):
    txt_files = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".txt")]
    total_files = len(txt_files)
    if total_files == 0:
        print(colored("Nenhum arquivo .txt encontrado no diretório selecionado.", 'red'))
        return []
    print(colored(f"Encontrados {total_files} arquivos .txt para escanear.", 'cyan'))
    all_found_lines = []
    max_processes = os.cpu_count() or 1
    with ProcessPoolExecutor(max_workers=max_processes) as executor:
        futures = {executor.submit(scan_file, file_path, keyword): file_path for file_path in txt_files}
        for i, future in enumerate(as_completed(futures), start=1):
            file_path = futures[future]
            try:
                found_lines = future.result()
                all_found_lines.extend(found_lines)
            except Exception as e:
                print(f"Erro ao processar o arquivo {file_path}: {e}")
            print(colored(f"Processando arquivo {i}/{total_files}", 'yellow'), end='\r')
    print()
    return all_found_lines

def extract_login_format(text):
    patterns = [
        r'([a-zA-Z0-9._@+-]+):([a-zA-Z0-9._@#$%^&*!+-]+)',
        r'([0-9]+):([^\s\|,;]+)',
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}):([^\s\|,;]+)',
        r'([a-zA-Z0-9._-]{3,}):([a-zA-Z0-9._@#$%^&*!+-]{3,})',
    ]
    found_credentials = []
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for login, password in matches:
            password = password.strip('.,;|[]{}()"\' \t\n\r')
            login = login.strip('.,;|[]{}()"\' \t\n\r')
            if (len(password) >= 3 and len(login) >= 3 and
                not any(c in login + password for c in ['http', 'www', '.txt', '.com']) and
                ':' not in password):
                found_credentials.append(f"{login}:{password}")
    return found_credentials

def filter_login_credentials(results):
    login_credentials = []
    print(colored(f"🔍 Analisando {len(results)} linhas em busca de credenciais...", 'cyan'))
    for i, line in enumerate(results):
        content = line.split('] ', 1)[1] if line.startswith('[') and '] ' in line else line
        credentials = extract_login_format(content)
        if credentials:
            login_credentials.extend(credentials)
            print(colored(f"✓ Linha {i+1}: {len(credentials)} credencial(is) encontrada(s)", 'green'))
    seen = set()
    unique_credentials = []
    for cred in login_credentials:
        if cred not in seen:
            unique_credentials.append(cred)
            seen.add(cred)
    return unique_credentials

def save_results(results, output_file, chk_file):
    try:
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(f"Resultados da busca - Total de ocorrências encontradas: {len(results)}\n")
            file.write("=" * 50 + "\n\n")
            for line in results:
                file.write(line + "\n")
        print(colored(f"✓ Arquivo completo salvo: '{output_file}'", 'green'))
        login_credentials = filter_login_credentials(results)
        if login_credentials:
            with open(chk_file, 'w', encoding='utf-8') as file:
                for credential in login_credentials:
                    file.write(credential + "\n")
            print(colored(f"🎯 {len(login_credentials)} credenciais únicas extraídas!", 'green'))
            print(colored(f"✓ Arquivo CHK salvo: '{chk_file}'", 'green'))
            return True, len(login_credentials)
        else:
            print(colored("⚠ Nenhuma credencial no formato email:senha encontrada nas linhas.", 'yellow'))
            print(colored("💡 Dica: Verifique se as linhas contêm formato email:senha", 'cyan'))
            print(colored("\n📋 Primeiras 3 linhas encontradas:", 'cyan'))
            for i, line in enumerate(results[:3]):
                print(colored(f"  {i+1}: {line[:100]}...", 'white'))
            return True, 0
    except Exception as e:
        print(colored(f"❌ Erro ao salvar arquivo: {e}", 'red'))
        return False, 0

def select_directory():
    root = tk.Tk()
    root.withdraw()
    directory = filedialog.askdirectory(title="Selecione o diretório contendo os arquivos .txt")
    return directory

def main():
    print(colored(banner, 'green'))
    directory = select_directory()
    if not directory:
        print(colored("Nenhum diretório foi selecionado.", 'red'))
        return
    print(colored(f"Diretório selecionado: {directory}", 'cyan'))
    keyword = input("Digite a palavra-chave: ").strip()
    if not keyword:
        print(colored("A palavra-chave não pode ser vazia.", 'red'))
        return
    safe_keyword = keyword.replace('.', '_').replace('/', '_').replace('\\', '_').replace(':', '_')
    output_file = os.path.join(directory, f"resultado_{safe_keyword}.txt")
    chk_file = os.path.join(directory, f"{safe_keyword}.chk")
    print(colored(f"Procurando por: '{keyword}'", 'cyan'))
    results = scan_files(directory, keyword)
    if results:
        success, credential_count = save_results(results, output_file, chk_file)
        if success:
            print(colored(f"\n✓ Encontradas {len(results)} ocorrências totais!", 'green'))
            print(colored(f"✓ Resultados completos salvos em: '{output_file}'", 'green'))
            if credential_count > 0:
                print(colored(f"✓ {credential_count} credenciais no formato CHK salvas em: '{chk_file}'", 'green'))
        else:
            print(colored("\n✗ Erro ao salvar os resultados.", 'red'))
    else:
        print(colored("\n✗ Nenhuma correspondência encontrada.", 'red'))
    input("\nPressione Enter para sair...")

if __name__ == "__main__":
    main()
