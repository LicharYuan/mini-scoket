from subprocess import check_output

def get_ip():
    # only test on local and remote docker
    ips = check_output(['hostname', '--all-ip-addresses'])
    ips = ips.decode("utf-8").strip()
    ips = ips.split(" ")[0]
    return ips
