// Simpan sebagai: src/routes/+page.server.js

/** @type {import('./$types').PageServerLoad} */
export async function load({ fetch }) {
    let ip = 'LOKAL (Bukan EC2)';
    
    try {
        // 'fetch' di sini berjalan di SISI SERVER (EC2),
        // jadi ia BISA mengakses alamat metadata AWS.
        // Kita set timeout 500ms agar tidak lambat jika gagal.
        const response = await fetch('http://169.254.169.254/latest/meta-data/local-ipv4', {
            signal: AbortSignal.timeout(500) 
        });
        
        if (response.ok) {
            ip = await response.text();
        }
    } catch (e) {
        // Ini normal jika kamu jalankan di 'npm run dev' di laptop lokal
        console.warn("Gagal mengambil IP metadata EC2 (normal jika dijalankan lokal)");
    }

    return {
        // Data ini akan otomatis dikirim ke +page.svelte
        serverIp: ip
    };
}