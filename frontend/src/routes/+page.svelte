<script>
  import { onMount } from 'svelte';
  // 1. Impor variabel .env secara aman menggunakan modul SvelteKit
  import { PUBLIC_API_BASE_URL } from '$env/static/public';

  // 2. Gunakan variabel yang sudah diimpor
  const API_BASE_URL = PUBLIC_API_BASE_URL;

  // --------------------------------------------------------
  // // --------------------------------------------------------
  /** @type {import('./$types').PageData} */
  export let data; // 'data' ini berisi { serverIp: '...' }


  // State untuk menyimpan data dari API
  let summaryData = { recent_sales: [], recent_salaries: [] };
  let salesReport = [];
  let salariesReport = [];

  // State untuk UI (loading & error)
  let isLoadingSummary = true;
  let isLoadingReport = false;
  let error = null;

  // Fungsi untuk mengambil data /summary (dari DynamoDB)
  async function fetchSummary() {
    isLoadingSummary = true;
    error = null;
    try {
      const res = await fetch(`${API_BASE_URL}/summary`);
      if (!res.ok) throw new Error(`Error HTTP: ${res.status} ${res.statusText}`);
      summaryData = await res.json();
    } catch (e) {
      error = e.message;
    } finally {
      isLoadingSummary = false;
    }
  }

  // Fungsi untuk mengambil data /report (dari RDS)
  async function fetchReport(type) {
    isLoadingReport = true;
    error = null;
    salesReport = []; // Reset tabel
    salariesReport = []; // Reset tabel

    try {
      const res = await fetch(`${API_BASE_URL}/report/${type}`);
      if (!res.ok) throw new Error(`Error HTTP: ${res.status} ${res.statusText}`);
      const dataApi = await res.json();
      
      if (type === 'sales') {
        salesReport = dataApi;
      } else if (type === 'salaries') {
        salariesReport = dataApi;
      }
    } catch (e) {
      error = e.message;
    } finally {
      isLoadingReport = false;
    }
  }

  // Jalankan `fetchSummary` saat halaman pertama kali dibuka
  onMount(() => {
    fetchSummary();
  });

  // Helper untuk format mata uang
  function formatCurrency(value) {
    const numberValue = Number(value) || 0;
    return new Intl.NumberFormat('id-ID', {
      style: 'currency',
      currency: 'IDR',
      minimumFractionDigits: 0,
    }).format(numberValue);
  }

  // Helper untuk format tanggal
  function formatDate(dateString) {
    return new Date(dateString).toLocaleString('id-ID', {
      dateStyle: 'medium',
      timeStyle: 'short',
    });
  }
</script>

<main>
  <h1>Dashboard Perusahaan</h1>

  <div class="server-info">
    Dilayani oleh instance: {data.serverIp}
  </div>


  {#if error}
    <div class="error-box">
      <strong>Error:</strong> {error}
    </div>
  {/if}

  <section>
    <h2>Ringkasan Cepat (dari DynamoDB)</h2>
    
    {#if isLoadingSummary}
      <p>Memuat ringkasan...</p>
    {:else}
      <div class="summary-grid">
        <div class="card">
          <h3>Penjualan Terkini</h3>
          <ul>
            {#each summaryData.recent_sales as sale (sale.sale_id)}
              <li>
                {sale.product_name}
                <span>{formatCurrency(sale.total_amount)}</span>
              </li>
            {:else}
              <li>Tidak ada data penjualan.</li>
            {/each}
          </ul>
        </div>
        
        <div class="card">
          <h3>Pembayaran Gaji Terkini</h3>
          <ul>
            {#each summaryData.recent_salaries as salary (salary.salary_id)}
              <li>
                {salary.employee_name}
                <span>{formatCurrency(salary.salary_amount)}</span>
              </li>
            {:else}
              <li>Tidak ada data gaji.</li>
            {/each}
          </ul>
        </div>
      </div>
    {/if}
  </section>

  <hr />

  <section>
    <h2>Laporan Detail (dari RDS)</h2>
    <div class="buttons">
      <button on:click={() => fetchReport('sales')} disabled={isLoadingReport}>
        {isLoadingReport && salariesReport.length === 0 ? 'Memuat...' : 'Muat Laporan Penjualan'}
      </button>
      <button on:click={() => fetchReport('salaries')} disabled={isLoadingReport}>
        {isLoadingReport && salesReport.length === 0 ? 'Memuat...' : 'Muat Laporan Gaji'}
      </button>
    </div>

    {#if salesReport.length > 0}
      <h3>Laporan Penjualan (100 Terakhir)</h3>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Produk</th>
            <th>Jml</th>
            <th>Total</th>
            <th>Waktu</th>
          </tr>
        </thead>
        <tbody>
          {#each salesReport as item (item.id)}
            <tr>
              <td>{item.id}</td>
              <td>{item.product_name}</td>
              <td>{item.quantity}</td>
              <td>{formatCurrency(item.total_amount)}</td>
              <td>{formatDate(item.sale_time)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}

    {#if salariesReport.length > 0}
      <h3>Laporan Gaji (100 Terakhir)</h3>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Karyawan</th>
            <th>Departemen</th>
            <th>Jumlah</th>
            <th>Waktu</th>
          </tr>
        </thead>
        <tbody>
          {#each salariesReport as item (item.id)}
            <tr>
              <td>{item.id}</td>
              <td>{item.employee_name}</td>
              <td>{item.department}</td>
              <td>{formatCurrency(item.salary_amount)}</td>
              <td>{formatDate(item.payment_time)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}

  </section>
</main>

<style>
  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background-color: #f9fafb;
    color: #111827;
    margin: 0;
  }

  main {
    max-width: 1000px;
    margin: 2rem auto;
    padding: 1.5rem;
    background-color: #ffffff;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  }

  h1 {
    color: #1f2937;
    border-bottom: 2px solid #e5e7eb;
    padding-bottom: 0.5rem;
  }

  h2 {
    color: #374151;
    margin-top: 2rem;
  }
  
  h3 {
    margin-top: 0;
  }

  /* -------------------------------------------------------- */
  /* 3. TAMBAHAN: Style untuk info IP */
  /* -------------------------------------------------------- */
  .server-info {
    font-size: 0.8rem;
    color: #6b7280; /* Abu-abu */
    text-align: right;
    margin-bottom: 1rem;
    font-family: monospace;
  }

  .summary-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
  }

  .card {
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    padding: 1rem;
  }

  .card ul {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .card li {
    display: flex;
    justify-content: space-between;
    padding: 0.5rem 0;
    border-bottom: 1px solid #f3f4f6;
  }
  .card li span {
    font-weight: 500;
  }
  .card li:last-child {
    border-bottom: none;
  }

  .buttons {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
  }

  button {
    font-size: 1rem;
    padding: 0.75rem 1.25rem;
    border: none;
    border-radius: 6px;
    background-color: #3b82f6;
    color: white;
    cursor: pointer;
    transition: background-color 0.2s;
  }
  button:hover:not(:disabled) {
    background-color: #2563eb;
  }
  button:disabled {
    background-color: #9ca3af;
    cursor: not-allowed;
  }

  .error-box {
    background: #fef2f2;
    color: #dc2626;
    border: 1px solid #fecaca;
    padding: 1rem;
    border-radius: 6px;
    margin-bottom: 1.5rem;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.02);
  }

  th, td {
    border: 1px solid #e5e7eb;
    padding: 0.75rem;
    text-align: left;
    vertical-align: top;
  }

  th {
    background-color: #f9fafb;
    font-weight: 600;
  }
  
  tr:nth-child(even) {
    background-color: #f9fafb;
  }
</style>