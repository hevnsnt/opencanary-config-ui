from flask import Flask, render_template, request, redirect, url_for, flash, make_response
import os
import json
import shutil
import glob
import copy

# 1) Define all defaults exactly as in your example
DEFAULT_CONFIG = {
    "device.node_id": "opencanary-1",

    # Git
    "git.enabled": False,
    "git.port": 9418,

    # FTP
    "ftp.enabled": False,
    "ftp.port": 21,
    "ftp.banner": "HOME FTP server ready for data",

    # HTTP
    "http.enabled": False,
    "http.port": 80,
    "http.banner": "Apache/2.2.22 (Ubuntu)",
    "http.skin": "nasLogin",

    # HTTP Proxy
    "httpproxy.enabled": False,
    "httpproxy.port": 8080,
    "httpproxy.skin": "squid",

    # Logger base (handlers filled dynamically)
    "logger": {
        "class": "PyLogger",
        "kwargs": {
            "formatters": {
                "plain": {"format": "%(message)s"},
                "syslog_rfc": {
                    "format": "opencanaryd[%(process)-5s:%(thread)d]: %(name)s %(levelname)-5s %(message)s"
                }
            },
            "handlers": {}
        }
    },

    # Portscan
    "portscan.enabled": False,
    "portscan.logfile": "/var/log/kern.log",
    "portscan.synrate": 5,
    "portscan.nmaposrate": 5,
    "portscan.lorate": 3,

    # SMB
    "smb.enabled": False,
    "smb.auditfile": "/var/log/samba-audit.log",

    # MySQL
    "mysql.enabled": False,
    "mysql.port": 3306,
    "mysql.banner": "5.5.43-0ubuntu0.14.04.1",

    # SSH
    "ssh.enabled": False,
    "ssh.port": 22,
    "ssh.version": "SSH-2.0-OpenSSH_5.1p1 Debian-4",

    # Redis
    "redis.enabled": False,
    "redis.port": 6379,

    # RDP
    "rdp.enabled": False,
    "rdp.port": 3389,

    # SIP
    "sip.enabled": False,
    "sip.port": 5060,

    # SNMP
    "snmp.enabled": False,
    "snmp.port": 161,

    # NTP
    "ntp.enabled": False,
    "ntp.port": 123,

    # TFTP
    "tftp.enabled": False,
    "tftp.port": 69,

    # TCP Banner
    "tcpbanner.enabled": False,
    "tcpbanner.maxnum": 10,

    # TCP Banner #1
    "tcpbanner_1.enabled": False,
    "tcpbanner_1.port": 8001,
    "tcpbanner_1.datareceivedbanner": "",
    "tcpbanner_1.initbanner": "",
    "tcpbanner_1.alertstring.enabled": False,
    "tcpbanner_1.alertstring": "",
    "tcpbanner_1.keep_alive.enabled": False,
    "tcpbanner_1.keep_alive_secret": "",
    "tcpbanner_1.keep_alive_probes": 11,
    "tcpbanner_1.keep_alive_interval": 300,
    "tcpbanner_1.keep_alive_idle": 300,

    # Telnet
    "telnet.enabled": False,
    "telnet.port": 23,
    "telnet.banner": "",
    "telnet.honeycreds": [
        {"username": "", "password": ""},
        {"username": "", "password": ""}
    ],

    # MSSQL
    "mssql.enabled": False,
    "mssql.version": "2012",
    "mssql.port": 1433,

    # VNC
    "vnc.enabled": False,
    "vnc.port": 5000,
}

# Simple services and their editable parameters
SERVICES = {
    'git': ['port'],
    'ftp': ['port', 'banner'],
    'http': ['port', 'banner', 'skin'],
    'httpproxy': ['port', 'skin'],
    'mysql': ['port', 'banner'],
    'ssh': ['port', 'version'],
    'redis': ['port'],
    'rdp': ['port'],
    'sip': ['port'],
    'snmp': ['port'],
    'ntp': ['port'],
    'tftp': ['port'],
    'mssql': ['port', 'version'],
    'vnc': ['port']
}

app = Flask(__name__)
app.secret_key = 'replace-with-a-secure-random-key'


def discover_skins():
    """Locate installed HTTP and HTTP proxy skins."""
    exe = shutil.which('opencanaryd')
    skins = {'http': [], 'httpproxy': []}
    if not exe:
        return skins

    root = os.path.dirname(os.path.dirname(exe))
    pattern = os.path.join(
        root, 'lib', 'python*', 'site-packages',
        'opencanary', 'modules', 'data', '*', 'skin'
    )
    for d in glob.glob(pattern):
        svc = os.path.basename(os.path.dirname(d))
        if svc in skins:
            for name in os.listdir(d):
                if os.path.isdir(os.path.join(d, name)):
                    skins[svc].append(name)
    return skins


@app.route('/', methods=['GET', 'POST'])
def configure():
    # Discover available skins
    skins = discover_skins()
    http_skins = skins['http']
    httpproxy_skins = skins['httpproxy']

    # Prepare email defaults for the form
    email_enabled = False
    email_config = {
        'host': '', 'port': 25,
        'fromaddr': '', 'toaddrs': [],
        'subject': 'OpenCanary Alert',
        'user': '', 'tls': False
    }

    if request.method == 'POST':
        # Start from defaults
        cfg = copy.deepcopy(DEFAULT_CONFIG)

        # Override Node ID
        node_id = request.form.get('node_id')
        if node_id:
            cfg['device.node_id'] = node_id

        # Services
        for svc, params in SERVICES.items():
            enabled = bool(request.form.get(f'{svc}_enabled'))
            cfg[f'{svc}.enabled'] = enabled
            for param in params:
                field = f'{svc}_{param}'
                val = request.form.get(field)
                if val is not None and val != '':
                    key = f'{svc}.{param}'
                    if isinstance(cfg[key], int):
                        cfg[key] = int(val)
                    else:
                        cfg[key] = val

        # Portscan
        if request.form.get('portscan_enabled'):
            cfg['portscan.enabled'] = True
        cfg['portscan.logfile'] = request.form.get('portscan_logfile', cfg['portscan.logfile'])
        cfg['portscan.synrate'] = int(request.form.get('portscan_synrate', cfg['portscan.synrate']))
        cfg['portscan.nmaposrate'] = int(request.form.get('portscan_nmaposrate', cfg['portscan.nmaposrate']))
        cfg['portscan.lorate'] = int(request.form.get('portscan_lorate', cfg['portscan.lorate']))

        # SMB
        if request.form.get('smb_enabled'):
            cfg['smb.enabled'] = True
        cfg['smb.auditfile'] = request.form.get('smb_auditfile', cfg['smb.auditfile'])

        # TCPBanner_1 JSON
        if request.form.get('tcpbanner_1_enabled'):
            cfg['tcpbanner_1.enabled'] = True
        tb1_json = request.form.get('tcpbanner_1_json', '')
        if tb1_json:
            try:
                data = json.loads(tb1_json)
                for k, v in data.items():
                    cfg[f'tcpbanner_1.{k}'] = v
            except json.JSONDecodeError:
                flash('Invalid JSON for TCPBanner_1', 'danger')

        # Telnet honeycreds
        if request.form.get('telnet_enabled'):
            cfg['telnet.enabled'] = True
        creds = request.form.get('telnet_honeycreds', '')
        if creds:
            try:
                cfg['telnet.honeycreds'] = json.loads(creds)
            except json.JSONDecodeError:
                flash('Invalid JSON for telnet honeycreds', 'danger')

        # Logging handlers + optional SMTP
        handlers = {}

        # Console is always on if checked
        if request.form.get('handler_console'):
            handlers['console'] = {
                'class': 'logging.StreamHandler',
                'stream': 'ext://sys.stdout'
            }

        # File handler with custom path
        if request.form.get('handler_file'):
            path = request.form.get('handler_file_path', '/var/tmp/opencanary.log')
            handlers['file'] = {
                'class': 'logging.FileHandler',
                'filename': path
            }

        # File2 handler with custom path
        if request.form.get('handler_file2'):
            path2 = request.form.get('handler_file2_path', '/var/tmp/opencanary-tmp.log')
            handlers['file2'] = {
                'class': 'logging.FileHandler',
                'filename': path2
            }
        if request.form.get('email_enabled'):
            email_enabled = True
            host = request.form.get('email_host')
            port = int(request.form.get('email_port', 25))
            email_config.update({
                'host': host,
                'port': port,
                'fromaddr': request.form.get('email_from'),
                'toaddrs': [x.strip() for x in request.form.get('email_to', '').split(',') if x],
                'subject': request.form.get('email_subject'),
                'user': request.form.get('email_user', ''),
                'tls': bool(request.form.get('email_tls'))
            })
            smtp = {
                'class': 'logging.handlers.SMTPHandler',
                'mailhost': [email_config['host'], email_config['port']],
                'fromaddr': email_config['fromaddr'],
                'toaddrs': email_config['toaddrs'],
                'subject': email_config['subject']
            }
            if email_config['user']:
                smtp['credentials'] = [email_config['user'], request.form.get('email_pass', '')]
            if email_config['tls']:
                smtp['secure'] = []
            handlers['SMTP'] = smtp

        cfg['logger']['kwargs']['handlers'] = handlers

        # Write out the config file
        #with open('opencanary.conf', 'w') as f:
        #    json.dump(cfg, f, indent=4)

        #flash('Configuration saved to ./opencanary.conf', 'success')
        #return redirect(url_for('configure'))
        
       # Return the config as a downloadable file
        data = json.dumps(cfg, indent=4)
        response = make_response(data)
        response.headers['Content-Disposition'] = 'attachment; filename=opencanary.conf'
        response.mimetype = 'application/json'
        return response
    
    # Render the form
    return render_template(
        'config_form.html',
        simple_services=SERVICES,
        http_skins=http_skins,
        httpproxy_skins=httpproxy_skins,
        default_config=DEFAULT_CONFIG,
        email_enabled=email_enabled,
        email_config=email_config
    )


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
