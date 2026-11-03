/** @odoo-module **/
/**
 * =============================================================================
 * TDB SOLUTION - CLIENT-SIDE PASSWORD ENCRYPTION FOR /web/login
 * Mã hóa mật khẩu phía trình duyệt trước khi gửi HTTP POST đến máy chủ
 * Ngăn chặn hoàn toàn việc hiển thị mật khẩu dạng Plain Text trong Network tab
 * =============================================================================
 */

(function () {
    'use strict';

    var SECURITY_KEY = 'TDB_SOLUTION_2026_SECURITY_SALT';

    // FIPS 180-2 SHA-256 thuần túy, đồng bộ 100%, không phụ thuộc thư viện ngoài
    function sha256Bytes(ascii) {
        function rightRotate(value, amount) {
            return (value >>> amount) | (value << (32 - amount));
        }
        var mathPow = Math.pow;
        var maxWord = mathPow(2, 32);
        var lengthProperty = 'length';
        var i, j;
        var words = [];
        var asciiBitLength = ascii[lengthProperty] * 8;
        var hash = [];
        var k = [];
        var primeCounter = 0;
        var isComposite = {};
        for (var candidate = 2; primeCounter < 64; candidate++) {
            if (!isComposite[candidate]) {
                for (i = 0; i < 313; i += candidate) {
                    isComposite[i] = candidate;
                }
                hash[primeCounter] = (mathPow(candidate, 0.5) * maxWord) | 0;
                k[primeCounter++] = (mathPow(candidate, 1 / 3) * maxWord) | 0;
            }
        }
        hash = hash.slice(0, 8);
        ascii += '\x80';
        while (ascii[lengthProperty] % 64 - 56) ascii += '\x00';
        for (i = 0; i < ascii[lengthProperty]; i++) {
            j = ascii.charCodeAt(i);
            words[i >> 2] |= j << ((3 - i % 4) * 8);
        }
        words[words[lengthProperty]] = (asciiBitLength / maxWord) | 0;
        words[words[lengthProperty]] = asciiBitLength | 0;
        for (j = 0; j < words[lengthProperty];) {
            var w = words.slice(j, j += 16);
            var oldHash = hash;
            hash = hash.slice(0, 8);
            for (i = 0; i < 64; i++) {
                var w15 = w[i - 15], w2 = w[i - 2];
                var s0 = rightRotate(w15, 7) ^ rightRotate(w15, 18) ^ (w15 >>> 3);
                var s1 = rightRotate(w2, 17) ^ rightRotate(w2, 19) ^ (w2 >>> 10);
                w[i] = (i < 16) ? w[i] : (w[i - 16] + s0 + w[i - 7] + s1) | 0;
                var s1_h = rightRotate(hash[4], 6) ^ rightRotate(hash[4], 11) ^ rightRotate(hash[4], 25);
                var ch = (hash[4] & hash[5]) ^ ((~hash[4]) & hash[6]);
                var temp1 = hash[7] + s1_h + ch + k[i] + w[i];
                var s0_h = rightRotate(hash[0], 2) ^ rightRotate(hash[0], 13) ^ rightRotate(hash[0], 22);
                var maj = (hash[0] & hash[1]) ^ (hash[0] & hash[2]) ^ (hash[1] & hash[2]);
                var temp2 = s0_h + maj;
                hash = [(temp1 + temp2) | 0].concat(hash);
                hash[4] = (hash[4] + temp1) | 0;
            }
            for (i = 0; i < 8; i++) {
                hash[i] = (hash[i] + oldHash[i]) | 0;
            }
        }
        var res = [];
        for (i = 0; i < 8; i++) {
            for (j = 3; j >= 0; j--) {
                res.push((hash[i] >> (8 * j)) & 255);
            }
        }
        return res;
    }

    function strToUtf8Bytes(str) {
        var binaryStr = unescape(encodeURIComponent(str));
        var bytes = [];
        for (var i = 0; i < binaryStr.length; i++) {
            bytes.push(binaryStr.charCodeAt(i));
        }
        return bytes;
    }

    function bytesToHex(bytes) {
        var hex = '';
        for (var i = 0; i < bytes.length; i++) {
            var h = bytes[i].toString(16);
            hex += (h.length === 1 ? '0' : '') + h;
        }
        return hex;
    }

    function getRandomHex(len) {
        var chars = '0123456789abcdef';
        var res = '';
        for (var i = 0; i < len; i++) {
            res += chars.charAt(Math.floor(Math.random() * chars.length));
        }
        return res;
    }

    function encryptPassword(plainText) {
        if (!plainText || plainText.indexOf('TDB_ENC:') === 0) {
            return plainText;
        }
        var salt = getRandomHex(16);
        var textBytes = strToUtf8Bytes(plainText);
        var out = [];
        var counter = 0;
        while (out.length < textBytes.length) {
            var seed = SECURITY_KEY + ':' + salt + ':' + counter;
            var block = sha256Bytes(seed);
            for (var b = 0; b < block.length; b++) {
                out.push(block[b]);
            }
            counter++;
        }
        var xorBytes = [];
        for (var i = 0; i < textBytes.length; i++) {
            xorBytes.push(textBytes[i] ^ out[i]);
        }
        return 'TDB_ENC:' + salt + ':' + bytesToHex(xorBytes);
    }

    // Lắng nghe sự kiện submit form đăng nhập ở pha capturing để mã hóa trước khi browser gửi POST
    document.addEventListener('submit', function (e) {
        var form = e.target;
        if (!form) return;

        // Bắt form đăng nhập của Odoo (.oe_login_form hoặc form có action /web/login)
        var isLoginForm = (form.classList && form.classList.contains('oe_login_form')) ||
            (form.action && form.action.indexOf('/web/login') !== -1);

        if (isLoginForm) {
            var passInput = form.querySelector('input[name="password"]');
            if (passInput && passInput.value && passInput.value.indexOf('TDB_ENC:') !== 0) {
                // Thay thế giá trị mật khẩu bằng token mã hóa
                passInput.value = encryptPassword(passInput.value);
            }
        }
    }, true);

    // Xuất ra window để các nút tự động / demo đăng nhập cũng có thể dùng
    window.tdbEncryptPassword = encryptPassword;
})();
