function base64Encode(str) {
    // 兼容中文base64
    return btoa(unescape(encodeURIComponent(str)));
}
function base64Decode(str) {
    return decodeURIComponent(escape(atob(str)));
}

function urlEncode(str) {
    return encodeURIComponent(str);
}
function doubleUrlEncode(str) {
    return encodeURIComponent(encodeURIComponent(str));
}

function getOutputCmd(type, input) {
    if (!input) return '';
    let b64 = base64Encode(input);
    switch(type) {
        case 'bash':
            // bash -c {echo,d2hvYW1p}|{base64,-d}|{bash,-i}
            return `bash -c {echo,${b64}}|{base64,-d}|{bash,-i}`;
        case 'sh':
            // sh -c $@|sh . echo whoami
            return `sh -c $@|sh . echo ${input}`;
        case 'powershell':
            // powershell.exe -NonI -W Hidden -NoP -Exec Bypass -Enc <base64>
            // 需UTF-16LE编码再base64
            let utf16le = new TextEncoder('utf-16le').encode(input);
            let arr = Array.from(utf16le).map(b => String.fromCharCode(b)).join('');
            let pwsh_b64 = btoa(arr);
            return `powershell.exe -NonI -W Hidden -NoP -Exec Bypass -Enc ${pwsh_b64}`;
        case 'python':
            // python -c exec('d2hvYW1p'.decode('base64'))
            return `python -c exec('${b64}'.decode('base64'))`;
        case 'perl':
            // perl -MMIME::Base64 -e eval(decode_base64('d2hvYW1p'))
            return `perl -MMIME::Base64 -e eval(decode_base64('${b64}'))`;
        default:
            return input;
    }
}

function encodeByType(str, type) {
    if (type === 'none') return str;
    if (type === 'url') return urlEncode(str);
    if (type === 'double_url') return doubleUrlEncode(str);
    if (type === 'base64') return base64Encode(str);
    return str;
}

// 命令类型自定义下拉菜单逻辑
const cmdTypeSelectBtn = document.getElementById('cmdTypeSelectBtn');
const cmdTypeSelectList = document.getElementById('cmdTypeSelectList');
const customCmdTypeSelect = document.getElementById('custom-cmdtype-select');
let cmdType = 'bash';

cmdTypeSelectBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    if (customCmdTypeSelect.classList.contains('open')) {
        customCmdTypeSelect.classList.remove('open');
    } else {
        customCmdTypeSelect.classList.add('open');
        cmdTypeSelectList.style.display = 'block';
    }
});

cmdTypeSelectList.querySelectorAll('li').forEach(function(li) {
    li.addEventListener('click', function(e) {
        cmdType = li.getAttribute('data-value');
        cmdTypeSelectBtn.textContent = li.textContent;
        cmdTypeSelectList.querySelectorAll('li').forEach(l => l.classList.remove('selected'));
        li.classList.add('selected');
        customCmdTypeSelect.classList.remove('open');
        cmdTypeSelectList.style.display = 'none';
        updateOutputCmd();
    });
});

document.addEventListener('click', function(e) {
    customCmdTypeSelect.classList.remove('open');
    cmdTypeSelectList.style.display = 'none';
});

function updateOutputCmd() {
    const inputCmd = document.getElementById('inputCmd').value.trim();
    const outputCmd = getOutputCmd(cmdType, inputCmd);
    document.getElementById('outputCmd').value = outputCmd;
    document.getElementById('finalCmd').value = '';
}

document.getElementById('inputCmd').addEventListener('input', updateOutputCmd);

// 自定义下拉菜单逻辑
const encodeSelectBtn = document.getElementById('encodeSelectBtn');
const encodeSelectList = document.getElementById('encodeSelectList');
const customSelect = document.getElementById('custom-encode-select');
let encodeType = 'none';

encodeSelectBtn.addEventListener('click', function(e) {
    e.stopPropagation();
    // 切换展开/收起
    if (customSelect.classList.contains('open')) {
        customSelect.classList.remove('open');
    } else {
        customSelect.classList.add('open');
        encodeSelectList.style.display = 'block'; // 确保展开时可见
    }
});

encodeSelectList.querySelectorAll('li').forEach(function(li) {
    li.addEventListener('click', function(e) {
        encodeType = li.getAttribute('data-value');
        encodeSelectBtn.textContent = li.textContent;
        encodeSelectList.querySelectorAll('li').forEach(l => l.classList.remove('selected'));
        li.classList.add('selected');
        customSelect.classList.remove('open');
        encodeSelectList.style.display = 'none'; // 收起
    });
});

document.addEventListener('click', function(e) {
    customSelect.classList.remove('open');
    encodeSelectList.style.display = 'none';
});

function encodeFinalCmd() {
    const outputCmd = document.getElementById('outputCmd').value;
    const finalCmd = encodeByType(outputCmd, encodeType);
    document.getElementById('finalCmd').value = finalCmd;
}

function copyOutput(id) {
    const output = document.getElementById(id);
    output.select();
    document.execCommand('copy');
    // 按钮变色+文字变化
    const btn = event.target;
    const oldText = btn.textContent;
    btn.textContent = '已复制';
    btn.classList.add('copy-success');
    btn.disabled = true;
    setTimeout(() => {
        btn.textContent = oldText;
        btn.classList.remove('copy-success');
        btn.disabled = false;
    }, 1200);
}

// 初始化
updateOutputCmd(); 