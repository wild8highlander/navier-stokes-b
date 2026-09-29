"use client";

import { useCallback, useRef, useState } from "react";
import { useFluidSim, type SimStats, type ViewMode } from "@/lib/fluid-engine";

type Lang = "en" | "ru";

const TXT = {
  en: {
    title: "Navier–Stokes Fluid Lab",
    sub: "Smagorinsky–Kolmogorov research program · 2D simulator",
    mode: "Mode",
    decay: "Decay · no force",
    forced: "Forced · mouse = force",
    stirrer: "Stirrer",
    reset: "Reset",
    pause: "Pause",
    resume: "Resume",
    vis: "Visualization",
    view: "View",
    part: "Tracer particles",
    arrows: "Velocity arrows",
    conf: "Vorticity confinement",
    visc: "Viscosity ν",
    speedL: "Simulation speed",
    spec: "Energy spectrum E(k)",
    modeDecay: "decay",
    modeForced: "forced",
    vort: "vorticity ω",
    speedM: "speed |u|",
    schlieren: "schlieren |∇ω|",
  },
  ru: {
    title: "Лаборатория Навье–Стокса",
    sub: "программа Смагоринского–Колмогорова · 2D-симулятор",
    mode: "Режим",
    decay: "Распад · без силы",
    forced: "Вынужденный · мышь = сила",
    stirrer: "Мешалка",
    reset: "Сброс",
    pause: "Пауза",
    resume: "Пуск",
    vis: "Визуализация",
    view: "Поле",
    part: "Частицы-трассеры",
    arrows: "Поле скорости",
    conf: "Удержание завихренности",
    visc: "Вязкость ν",
    speedL: "Скорость расчёта",
    spec: "Энергетический спектр E(k)",
    modeDecay: "распад",
    modeForced: "вынужденный",
    vort: "завихренность ω",
    speedM: "скорость |u|",
    schlieren: "шлирен |∇ω|",
  },
};

export default function Home() {
  const [lang, setLang] = useState<Lang>("en");
  const t = TXT[lang];
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const specRef = useRef<HTMLCanvasElement>(null);
  const [stats, setStats] = useState<SimStats>({
    t: 0, E: 0, enstrophy: 0, reynolds: 0, fps: 0, slope: NaN,
  });
  const onStats = useCallback((s: SimStats) => {
    setStats(s);
  }, []);

  const [forced, setForced] = useState(false);
  const [stirrer, setStirrer] = useState(false);
  const [paused, setPaused] = useState(false);
  const [view, setView] = useState<ViewMode>("vort");
  const [particles, setParticles] = useState(true);
  const [arrows, setArrows] = useState(false);
  const [conf, setConf] = useState(0.12);
  const [viscExp, setViscExp] = useState(-5);
  const [speedMul, setSpeedMul] = useState(1);

  const { reset, pointerHandlers } = useFluidSim(
    canvasRef,
    specRef,
    {
      nu: Math.pow(10, viscExp),
      confinement: conf,
      speedMul,
      forced,
      stirrer,
      paused,
      view,
      particles,
      arrows,
    },
    onStats,
  );

  const btn = (on: boolean) =>
    `rounded-lg border px-3 py-2 text-[12.5px] transition-colors ${
      on
        ? "border-[#92761f] bg-[#92761f]/10 text-[#d3a945]"
        : "border-[#2e3340] bg-[#232730] text-[#e9e7e1] hover:border-[#92761f]"
    }`;

  return (
    <div className="min-h-screen flex flex-col bg-[#131519] text-[#e9e7e1]">
      <header className="flex flex-wrap items-baseline gap-3 border-b border-[#2e3340] px-5 py-3">
        <h1 className="text-[17px] font-semibold">
          <b className="text-[#d3a945]">Navier–Stokes</b> Fluid Lab
        </h1>
        <span className="text-xs text-[#9aa0ac]">{t.sub}</span>
        <span className="ml-auto flex gap-1.5">
          {(["en", "ru"] as Lang[]).map((l) => (
            <button
              key={l}
              onClick={() => setLang(l)}
              className={`rounded-md border px-2.5 py-1 text-[11px] ${
                lang === l
                  ? "border-[#92761f] text-[#d3a945]"
                  : "border-[#2e3340] text-[#9aa0ac]"
              }`}
            >
              {l.toUpperCase()}
            </button>
          ))}
        </span>
      </header>

      <main className="grid flex-1 grid-cols-1 items-start gap-3.5 p-4 lg:grid-cols-[1fr_330px]">
        <section className="rounded-[10px] border border-[#2e3340] bg-[#1c1f26] p-2.5">
          <canvas
            ref={canvasRef}
            width={1024}
            height={640}
            className="block w-full cursor-crosshair touch-none rounded-md bg-[#0d0f13]"
            {...pointerHandlers}
          />
          <div className="mt-2.5 flex flex-wrap items-center gap-2">
            <span className="rounded-md border border-[#2e3340] bg-[#232730] px-2.5 py-1 text-[11.5px] text-[#9aa0ac]">
              <b className="font-semibold text-[#e9e7e1]">{t.mode}:</b>{" "}
              {forced ? t.modeForced : t.modeDecay}
            </span>
            <span className="rounded-md border border-[#2e3340] bg-[#232730] px-2.5 py-1 text-[11.5px] tabular-nums text-[#9aa0ac]">
              <b className="text-[#e9e7e1]">t</b> = {stats.t.toFixed(1)}
            </span>
            <span className="rounded-md border border-[#2e3340] bg-[#232730] px-2.5 py-1 text-[11.5px] tabular-nums text-[#9aa0ac]">
              <b className="text-[#e9e7e1]">E</b> = {stats.E.toExponential(2)}
            </span>
            <span className="rounded-md border border-[#2e3340] bg-[#232730] px-2.5 py-1 text-[11.5px] tabular-nums text-[#9aa0ac]">
              <b className="text-[#e9e7e1]">Ω</b> ={" "}
              {stats.enstrophy.toExponential(2)}
            </span>
            <span className="rounded-md border border-[#2e3340] bg-[#232730] px-2.5 py-1 text-[11.5px] tabular-nums text-[#9aa0ac]">
              <b className="text-[#e9e7e1]">Re</b> ≈{" "}
              {stats.reynolds > 1 ? Math.round(stats.reynolds) : "—"}
            </span>
            <span className="rounded-md border border-[#2e3340] bg-[#232730] px-2.5 py-1 text-[11.5px] tabular-nums text-[#9aa0ac]">
              <b className="text-[#e9e7e1]">FPS</b> = {stats.fps.toFixed(0)}
            </span>
          </div>
        </section>

        <aside className="flex flex-col gap-3">
          <div className="rounded-[10px] border border-[#2e3340] bg-[#1c1f26] p-3.5">
            <h2 className="mb-2.5 text-[11px] font-bold uppercase tracking-[1.4px] text-[#d3a945]">
              {t.mode}
            </h2>
            <div className="flex flex-wrap gap-2">
              <button className={btn(!forced)} onClick={() => setForced(false)}>
                {t.decay}
              </button>
              <button className={btn(forced)} onClick={() => setForced(true)}>
                {t.forced}
              </button>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                className={btn(stirrer)}
                onClick={() => {
                  setStirrer(!stirrer);
                  if (!stirrer) setForced(true);
                }}
              >
                {t.stirrer}: {stirrer ? "on" : "off"}
              </button>
              <button className={btn(false)} onClick={() => reset()}>
                {t.reset}
              </button>
              <button
                className={btn(paused)}
                onClick={() => setPaused(!paused)}
              >
                {paused ? t.resume : t.pause}
              </button>
            </div>
          </div>

          <div className="rounded-[10px] border border-[#2e3340] bg-[#1c1f26] p-3.5">
            <h2 className="mb-2.5 text-[11px] font-bold uppercase tracking-[1.4px] text-[#d3a945]">
              {t.vis}
            </h2>
            <label className="mb-1 flex justify-between text-[11.5px] text-[#9aa0ac]">
              <span>{t.view}</span>
            </label>
            <select
              value={view}
              onChange={(e) => setView(e.target.value as ViewMode)}
              className="w-full rounded-md border border-[#2e3340] bg-[#232730] px-2 py-1.5 text-[12.5px]"
            >
              <option value="vort">{t.vort}</option>
              <option value="speed">{t.speedM}</option>
              <option value="schlieren">{t.schlieren}</option>
            </select>
            <div className="mt-2 flex flex-wrap gap-2">
              <button className={btn(particles)} onClick={() => setParticles(!particles)}>
                {t.part}
              </button>
              <button className={btn(arrows)} onClick={() => setArrows(!arrows)}>
                {t.arrows}
              </button>
            </div>
            <label className="mb-1 mt-3 flex justify-between text-[11.5px] text-[#9aa0ac]">
              <span>{t.conf}</span>
              <b className="font-semibold text-[#e9e7e1]">{conf.toFixed(2)}</b>
            </label>
            <input
              type="range"
              min={0}
              max={0.4}
              step={0.01}
              value={conf}
              onChange={(e) => setConf(parseFloat(e.target.value))}
              className="w-full accent-[#92761f]"
            />
            <label className="mb-1 mt-2 flex justify-between text-[11.5px] text-[#9aa0ac]">
              <span>{t.visc}</span>
              <b className="font-semibold text-[#e9e7e1]">
                {Math.pow(10, viscExp).toExponential(1)}
              </b>
            </label>
            <input
              type="range"
              min={-5}
              max={-2.7}
              step={0.05}
              value={viscExp}
              onChange={(e) => setViscExp(parseFloat(e.target.value))}
              className="w-full accent-[#92761f]"
            />
            <label className="mb-1 mt-2 flex justify-between text-[11.5px] text-[#9aa0ac]">
              <span>{t.speedL}</span>
              <b className="font-semibold text-[#e9e7e1]">{speedMul.toFixed(1)}×</b>
            </label>
            <input
              type="range"
              min={0.2}
              max={2.5}
              step={0.1}
              value={speedMul}
              onChange={(e) => setSpeedMul(parseFloat(e.target.value))}
              className="w-full accent-[#92761f]"
            />
          </div>

          <div className="rounded-[10px] border border-[#2e3340] bg-[#1c1f26] p-3.5">
            <h2 className="mb-2.5 text-[11px] font-bold uppercase tracking-[1.4px] text-[#d3a945]">
              {t.spec}
            </h2>
            <canvas
              ref={specRef}
              width={600}
              height={330}
              className="block w-full rounded-md bg-[#0d0f13]"
            />
            <div className="mt-2 flex flex-wrap gap-3 text-[11px] text-[#9aa0ac]">
              <span>
                <i className="mr-1.5 inline-block h-[3px] w-[18px] rounded-sm bg-[#d3a945] align-middle" />
                E(k)
              </span>
              <span>
                <i className="mr-1.5 inline-block h-[3px] w-[18px] rounded-sm bg-[#4db3d6] align-middle" />
                k⁻⁵ᐟ³
              </span>
              <span>
                <i className="mr-1.5 inline-block h-[3px] w-[18px] rounded-sm bg-[#d46a5f] align-middle" />
                k⁻³
              </span>
              <span className="ml-auto tabular-nums text-[#e9e7e1]">
                slope = {isFinite(stats.slope) ? stats.slope.toFixed(2) : "—"}
              </span>
            </div>
          </div>
        </aside>
      </main>

      <footer className="mt-auto border-t border-[#2e3340] px-5 py-3 text-[11px] leading-relaxed text-[#9aa0ac]">
        2D Navier–Stokes on a periodic 256×160 lattice: semi-Lagrangian
        advection, Jacobi pressure projection, vorticity confinement. Part of
        the{" "}
        <a
          className="text-[#4db3d6] hover:underline"
          href="https://github.com/wild8highlander/navier-stokes-b"
          target="_blank"
          rel="noreferrer"
        >
          navier-stokes-b
        </a>{" "}
        Smagorinsky–Kolmogorov research program.
      </footer>
    </div>
  );
}
