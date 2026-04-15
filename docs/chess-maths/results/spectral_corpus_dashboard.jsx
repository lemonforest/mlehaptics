import { useState, useMemo } from "react";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ScatterChart, Scatter, AreaChart, Area, Legend } from "recharts";
import { GAMES } from "./spectral_corpus_dashboard.data.js";

const GLOBAL_MAX_PLY = Math.max(...GAMES.map(g => g.n));



const COLORS = ['#e6194b','#3cb44b','#4363d8','#f58231','#911eb4','#42d4f4','#f032e6','#bfef45','#469990','#dcbeff'];

// Build a recharts row array keyed by true ply values (no grid forcing,
// no nearest-neighbor lookup). Union of every active game's plies; each
// game contributes a value only at plies it actually has. Relies on
// generator-side uniform stride so indexOf hits on every row.
function buildSeries(activeGames, channel) {
  const allPlies = new Set();
  activeGames.forEach(g => g.plies.forEach(p => allPlies.add(p)));
  const plies = [...allPlies].sort((a, b) => a - b);
  return plies.map(p => {
    const row = { ply: p };
    activeGames.forEach(g => {
      const i = g.plies.indexOf(p);
      if (i >= 0) row[`g${g.id}`] = g[channel][i];
    });
    return row;
  });
}

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'rgba(15,15,20,0.95)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 6, padding: '8px 12px', fontSize: 11 }}>
      <div style={{ color: '#999', marginBottom: 4 }}>Ply {label}</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }}>{p.name}: {p.value?.toFixed(2)}</div>
      ))}
    </div>
  );
};

const ScatterTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{ background: 'rgba(15,15,20,0.95)', border: '1px solid rgba(255,255,255,0.15)', borderRadius: 6, padding: '8px 12px', fontSize: 11 }}>
      <div style={{ color: '#999', marginBottom: 4 }}>Progress {(label * 100).toFixed(0)}%</div>
      {payload.map((p, i) => (
        <div key={i} style={{ color: p.color }}>{p.name}: {p.value?.toFixed(2)}</div>
      ))}
    </div>
  );
};

export default function SpectralDashboard() {
  const [view, setView] = useState('a1');
  const [selected, setSelected] = useState(new Set(GAMES.map(g => g.id)));

  const toggle = (id) => {
    setSelected(prev => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const activeGames = GAMES.filter(g => selected.has(g.id));

  const a1Data = useMemo(() => buildSeries(activeGames, 'a1'), [activeGames]);

  const chaosData = useMemo(() => {
    const rows = [];
    activeGames.forEach(g => {
      for (let i = 0; i < g.ft.length; i++) {
        const ir = g.it[i] || 0.01;
        rows.push({ ply: g.plies[i], ratio: g.ft[i] / ir, game: g.id, pct: g.plies[i] / g.n });
      }
    });
    return rows;
  }, [activeGames]);

  const fiberData = useMemo(() => buildSeries(activeGames, 'ft'), [activeGames]);
  const faData    = useMemo(() => buildSeries(activeGames, 'fa'), [activeGames]);

  const views = {
    a1: { title: 'A₁ Energy — D4-Invariant Complexity', data: a1Data, key: 'a1', yLabel: 'Energy', desc: 'Total symmetric complexity — board signal averaged over all 8 D4 transforms. Predicts tactical depth in §9g depth-gap experiment (N=55 Stockfish positions, ρ=+0.452, p=0.0005). Not derived from this corpus.' },
    fiber: { title: 'Total Fiber Energy — Interaction Topology', data: fiberData, key: 'ft', yLabel: 'Energy', desc: 'Measures cross-piece interaction strength. Drops as pieces are exchanged.' },
    fa: { title: 'Pawn Antisymmetric Fiber — Z₂ Breaking', data: faData, key: 'fa', yLabel: 'Energy', desc: 'The only channel unique to pawns. Monotonically decreases as pawns leave the board.' },
  };

  const v = views[view];
  const chartData = v.data;

  return (
    <div style={{ background: '#0a0a0f', color: '#e0e0e0', minHeight: '100vh', fontFamily: "'JetBrains Mono', 'Fira Code', monospace", padding: 20 }}>
      <div style={{ maxWidth: 900, margin: '0 auto' }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: '#fff', letterSpacing: 1, margin: '0 0 4px' }}>
          SPECTRAL LATTICE FERMION CORPUS
        </h1>
        <div style={{ fontSize: 11, color: '#666', marginBottom: 16 }}>
          {GAMES.length} games · 640-dim encoding · 10 channels × 64 eigenmodes
        </div>

        {/* Game selector */}
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
          {GAMES.map((g, i) => (
            <button key={g.id} onClick={() => toggle(g.id)}
              style={{
                background: selected.has(g.id) ? COLORS[i] + '22' : 'transparent',
                border: `1px solid ${selected.has(g.id) ? COLORS[i] : '#333'}`,
                color: selected.has(g.id) ? COLORS[i] : '#555',
                borderRadius: 4, padding: '3px 8px', fontSize: 10, cursor: 'pointer',
                transition: 'all 0.15s'
              }}>
              G{g.id} · {g.n}p · χ={g.cr}
            </button>
          ))}
        </div>

        {/* View tabs */}
        <div style={{ display: 'flex', gap: 2, marginBottom: 12 }}>
          {Object.entries(views).map(([k, vv]) => (
            <button key={k} onClick={() => setView(k)}
              style={{
                background: view === k ? '#1a1a2e' : 'transparent',
                border: view === k ? '1px solid #333' : '1px solid transparent',
                color: view === k ? '#fff' : '#666',
                borderRadius: 4, padding: '6px 14px', fontSize: 11, cursor: 'pointer',
                borderBottom: view === k ? '2px solid #4363d8' : '2px solid transparent'
              }}>
              {k === 'a1' ? 'A₁ Complexity' : k === 'fiber' ? 'Fiber Topology' : 'Pawn Z₂'}
            </button>
          ))}
          <button onClick={() => setView('chaos')}
            style={{
              background: view === 'chaos' ? '#1a1a2e' : 'transparent',
              border: view === 'chaos' ? '1px solid #333' : '1px solid transparent',
              color: view === 'chaos' ? '#fff' : '#666',
              borderRadius: 4, padding: '6px 14px', fontSize: 11, cursor: 'pointer',
              borderBottom: view === 'chaos' ? '2px solid #4363d8' : '2px solid transparent'
            }}>
            Chaos Ratio
          </button>
        </div>

        {/* Chart */}
        <div style={{ background: '#0f0f18', border: '1px solid #1a1a2e', borderRadius: 8, padding: '16px 8px 8px' }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#ccc', marginBottom: 2, paddingLeft: 8 }}>
            {view === 'chaos' ? 'Dynamic Chaos Ratio (Fiber / Irrep)' : v.title}
          </div>
          <div style={{ fontSize: 10, color: '#555', marginBottom: 12, paddingLeft: 8 }}>
            {view === 'chaos'
              ? 'Per-ply fiber÷irrep energy. High = sharp/tactical, low = positional. Outliers (χ ≫ corpus median) mark unusually sharp games.'
              : v.desc}
          </div>

          <ResponsiveContainer width="100%" height={320}>
            {view === 'chaos' ? (
              <ScatterChart margin={{ top: 5, right: 20, bottom: 20, left: 40 }}>
                <XAxis dataKey="pct" type="number" domain={[0, 1]} tick={{ fontSize: 10, fill: '#555' }}
                  label={{ value: 'Game Progress', position: 'bottom', offset: 0, style: { fontSize: 10, fill: '#666' } }} />
                <YAxis dataKey="ratio" type="number" domain={[0, 'auto']} tick={{ fontSize: 10, fill: '#555' }}
                  label={{ value: 'Fiber / Irrep', angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: '#666' } }} />
                <Tooltip content={<ScatterTooltip />} />
                {activeGames.map((g, i) => {
                  const gd = chaosData.filter(d => d.game === g.id);
                  return <Scatter key={g.id} name={`G${g.id}`} data={gd} fill={COLORS[GAMES.findIndex(gg => gg.id === g.id)]} opacity={0.5} r={2} />;
                })}
              </ScatterChart>
            ) : (
              <LineChart data={chartData} margin={{ top: 5, right: 20, bottom: 20, left: 40 }}>
                <XAxis dataKey="ply" type="number" domain={[0, GLOBAL_MAX_PLY]} allowDataOverflow={false}
                  tick={{ fontSize: 10, fill: '#555' }}
                  label={{ value: 'Ply', position: 'bottom', offset: 0, style: { fontSize: 10, fill: '#666' } }} />
                <YAxis tick={{ fontSize: 10, fill: '#555' }}
                  label={{ value: v.yLabel, angle: -90, position: 'insideLeft', style: { fontSize: 10, fill: '#666' } }} />
                <Tooltip content={<CustomTooltip />} />
                {activeGames.map((g, i) => (
                  <Line key={g.id} type="monotone" dataKey={`g${g.id}`} name={`G${g.id}`}
                    stroke={COLORS[GAMES.findIndex(gg => gg.id === g.id)]} strokeWidth={1.5} dot={false} opacity={0.8}
                    connectNulls />
                ))}
              </LineChart>
            )}
          </ResponsiveContainer>
        </div>

        {/* Stats table */}
        <div style={{ marginTop: 16, background: '#0f0f18', border: '1px solid #1a1a2e', borderRadius: 8, padding: 12, overflowX: 'auto' }}>
          <div style={{ fontSize: 12, fontWeight: 600, color: '#999', marginBottom: 8 }}>Per-Game Summary</div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 10 }}>
            <thead>
              <tr style={{ color: '#666', borderBottom: '1px solid #1a1a2e' }}>
                <th style={{ textAlign: 'left', padding: '4px 8px' }}>Game</th>
                <th style={{ textAlign: 'right', padding: '4px 8px' }}>Plies</th>
                <th style={{ textAlign: 'right', padding: '4px 8px' }}>χ ratio</th>
                <th style={{ textAlign: 'right', padding: '4px 8px' }}>A₁ peak</th>
                <th style={{ textAlign: 'right', padding: '4px 8px' }}>Peak ply</th>
                <th style={{ textAlign: 'right', padding: '4px 8px' }}>FA start</th>
                <th style={{ textAlign: 'right', padding: '4px 8px' }}>FA end</th>
                <th style={{ textAlign: 'right', padding: '4px 8px' }}>FA Δ%</th>
              </tr>
            </thead>
            <tbody>
              {GAMES.map((g, i) => {
                const a1Peak = Math.max(...g.a1);
                const peakPly = g.plies[g.a1.indexOf(a1Peak)];
                const faStart = g.fa[0];
                const faEnd = g.fa[g.fa.length - 1];
                const faDelta = ((faEnd - faStart) / faStart * 100);
                return (
                  <tr key={g.id} style={{
                    color: selected.has(g.id) ? COLORS[i] : '#444',
                    borderBottom: '1px solid #111', cursor: 'pointer',
                    opacity: selected.has(g.id) ? 1 : 0.4
                  }} onClick={() => toggle(g.id)}>
                    <td style={{ padding: '4px 8px' }}>G{g.id}</td>
                    <td style={{ textAlign: 'right', padding: '4px 8px' }}>{g.n}</td>
                    <td style={{ textAlign: 'right', padding: '4px 8px', color: g.cr > 5 ? '#f58231' : undefined }}>{g.cr.toFixed(2)}</td>
                    <td style={{ textAlign: 'right', padding: '4px 8px' }}>{a1Peak.toFixed(2)}</td>
                    <td style={{ textAlign: 'right', padding: '4px 8px' }}>{peakPly}</td>
                    <td style={{ textAlign: 'right', padding: '4px 8px' }}>{faStart.toFixed(2)}</td>
                    <td style={{ textAlign: 'right', padding: '4px 8px' }}>{faEnd.toFixed(2)}</td>
                    <td style={{ textAlign: 'right', padding: '4px 8px', color: faDelta < -30 ? '#e6194b' : '#3cb44b' }}>{faDelta.toFixed(0)}%</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <div style={{ fontSize: 9, color: '#444', marginTop: 12, textAlign: 'center' }}>
          Chess Spectral Lattice Fermion Research · mlehaptics Project · April 2026
        </div>
      </div>
    </div>
  );
}
