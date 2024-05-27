import platform
import socket
import subprocess
import winreg as reg
import scapy.all as sc

# Получаем локальный IP-адрес
def local_ipv4():
    st = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        st.connect(('10.255.255.255', 1))
        ip_l = st.getsockname()[0]
    except Exception:
        ip_l = '127.0.0.1'
    finally:
        st.close()
    return ip_l

# Получаем адрес шлюза по умолчанию для Windows
def get_gateway_win():
    com = f'route PRINT 0* | findstr {local_ipv4()}'.split()
    return subprocess.check_output(com, shell=True).decode('cp866').split()[2]

# Получаем адрес шлюза по умолчанию для Linux
def get_gateway_linx():
    com = 'route -n'.split()
    return str(subprocess.check_output(com, shell=True)).split("\\n")[2].split()[1].strip()

# Сканируем сеть, получаем IP и MAC сетевых машин
def get_ip_mac_network(ip):
    answered_list = sc.srp(sc.Ether(dst='ff:ff:ff:ff:ff:ff') / sc.ARP(pdst=ip), timeout=1, verbose=False)[0]
    clients_list = []
    for element in answered_list:
        clients_list.append({'ip': element[1].psrc, 'mac': element[1].hwsrc})
    return clients_list

# Проверяем наличие программы на устройстве (локально или удалённо)
def check_program(ip_address, program_name):
    if ip_address == local_ipv4():
        return check_program_locally(program_name)
    else:
        return check_program_remotely(ip_address, program_name)

# Проверяем наличие программы локально на устройстве
def check_program_locally(program_name):
    try:
        reg_key = reg.HKEY_LOCAL_MACHINE
        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        with reg.ConnectRegistry(None, reg_key) as reg_handle:
            with reg.OpenKey(reg_handle, reg_path, 0, reg.KEY_READ) as reg_subkey:
                for i in range(reg.QueryInfoKey(reg_subkey)[0]):
                    subkey_name = reg.EnumKey(reg_subkey, i)
                    with reg.OpenKey(reg_handle, f"{reg_path}\\{subkey_name}") as app_key:
                        try:
                            display_name = reg.QueryValueEx(app_key, "DisplayName")[0]
                            if program_name.lower() in display_name.lower():
                                return True
                        except OSError:
                            pass
    except Exception as e:
        print(f"Error checking program locally: {e}")
    
    return False

# Проверяем наличие программы на удалённом устройстве
def check_program_remotely(ip_address, program_name):
    command = f'where /q \\{ip_address} "{program_name}"'
    try:
        output = subprocess.check_output(command, shell=True, universal_newlines=True, timeout=5, stderr=subprocess.STDOUT)
        if output.strip():
            return True
        else:
            return False
    except subprocess.CalledProcessError:
        return False
    except subprocess.TimeoutExpired:
        return False

# Выводим IP, MAC и информацию о программе для каждого компьютера в сети
def print_ip_mac_with_program(mac_ip_list, program_name):
    print(f"\nMachines in Network:\n\nIP\t\t\t\t\tMAC-address\t\tProgram Installed\n{'-' * 70}")
    for client in mac_ip_list:
        program_installed = check_program(client["ip"], program_name)
        print(f'{client["ip"]}\t\t{client["mac"]}\t\t{"Yes" if program_installed else "No"}')

    # Проверяем наличие программы на локальном устройстве
    program_installed_local = check_program(local_ipv4(), program_name)
    print(f'\nLocal Machine ({local_ipv4()}):\nProgram "{program_name}" installed: {"Yes" if program_installed_local else "No"}')

# Основная функция
def main():
    local_ip = local_ipv4()
    if platform.system() == "Windows":
        gateway = get_gateway_win()
    elif platform.system() == 'Linux':
        gateway = get_gateway_linx()
    program_name = input("Введите название программы для проверки: ").strip()
    ip_mac_network = get_ip_mac_network(f'{local_ip.split(".")[0]}.{local_ip.split(".")[1]}.{local_ip.split(".")[2]}.1/24')
    print(f'\n[+] Local IP: {local_ip}\n[+] Local Gateway: {gateway}')
    print_ip_mac_with_program(ip_mac_network, program_name)

if __name__ == "__main__":
    main()
