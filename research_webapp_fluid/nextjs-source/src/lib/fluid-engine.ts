"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/* =====================================================================
   2D Navier-Stokes solver engine (Stable Fluids + vorticity
   confinement), radix-2 FFT spectrum, tracer particles.
   Ported from the standalone research_webapp_fluid/index.html.
   ===================================================================== */

const W = 256;
const H = 160;
const DT = 0.016;
const NP = 3600;
const SW = 128;

export type ViewMode = "vort" | "speed" | "schlieren";

export interface SimStats {
  t: number;
  E: number;
  enstrophy: number;
  reynolds: number;
  fps: number;
  slope: number;
}

export interface SimParams {
  nu: number;
  confinement: number;
  speedMul: number;
  forced: boolean;
  stirrer: boolean;
  paused: boolean;
  view: ViewMode;
  particles: boolean;
  arrows: boolean;
}

export function useFluidSim(
  canvasRef: React.RefObject<HTMLCanvasElement | null>,
  specRef: React.RefObject<HTMLCanvasElement | null>,
  params: SimParams,
  onStats: (s: SimStats) => void,
) {
  const paramsRef = useRef(params);
  paramsRef.current = params;

  const state = useRef({
    u: new Float32Array(W * H),
    v: new Float32Array(W * H),
    u2: new Float32Array(W * H),
    v2: new Float32Array(W * H),
    p: new Float32Array(W * H),
    div: new Float32Array(W * H),
    w: new Float32Array(W * H),
    fx: new Float32Array(W * H),
    fy: new Float32Array(NP > 0 ? W * H : 0),
    px: new Float32Array(NP),
    py: new Float32Array(NP),
    page: new Float32Array(NP),
    kre: new Float64Array(SW * SW),
    kim: new Float64Array(SW * SW),
    kre2: new Float64Array(SW * SW),
    kim2: new Float64Array(SW * SW),
    EKsm: new Float64Array(SW / 2),
    EK: new Float64Array(SW / 2),
    t: 0,
    ready: false,
    frames: 0,
  });

  const mouse = useRef({ down: false, x: 0, y: 0, px: 0, py: 0 });

  const IX = (x: number, y: number) => x + y * W;
  const wrap = (i: number, m: number) => ((i % m) + m) % m;

  const sample = useCallback((f: Float32Array, x: number, y: number) => {
    const i = Math.floor(x);
    const j = Math.floor(y);
    const fxr = x - i;
    const fyr = y - j;
    const i0 = wrap(i, W);
    const i1 = wrap(i + 1, W);
    const j0 = wrap(j, H);
    const j1 = wrap(j + 1, H);
    const a = f[IX(i0, j0)];
    const b = f[IX(i1, j0)];
    const c = f[IX(i0, j1)];
    const d = f[IX(i1, j1)];
    return (
      (a * (1 - fxr) + b * fxr) * (1 - fyr) +
      (c * (1 - fxr) + d * fxr) * fyr
    );
  }, []);

  const reset = useCallback(() => {
    const s = state.current;
    s.u.fill(0);
    s.v.fill(0);
    s.p.fill(0);
    s.fx.fill(0);
    s.fy.fill(0);
    s.t = 0;
    s.ready = false;
    const nG = 4;
    for (let j = 0; j < H; j++) {
      for (let i = 0; i < W; i++) {
        const x = (i / W) * 2 * Math.PI;
        const y = (j / H) * 2 * Math.PI;
        s.u[IX(i, j)] = Math.sin(nG * y) * Math.cos(nG * x) * 0.9;
        s.v[IX(i, j)] = -Math.cos(nG * y) * Math.sin(nG * x) * 0.9;
      }
    }
    for (let c = 0; c < W * H; c++) {
      s.u[IX(c % W, Math.floor(c / W))] +=
        (Math.random() - 0.5) * 0.3;
      s.v[IX(c % W, Math.floor(c / W))] +=
        (Math.random() - 0.5) * 0.3;
    }
    for (let n = 0; n < NP; n++) {
      s.px[n] = Math.random() * W;
      s.py[n] = Math.random() * H;
      s.page[n] = Math.random();
    }
  }, []);

  useEffect(() => {
    reset();
  }, [reset]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const specCanvas = specRef.current;
    if (!canvas || !specCanvas) return;
    const ctx = canvas.getContext("2d");
    const sctx = specCanvas.getContext("2d");
    if (!ctx || !sctx) return;

    const img = ctx.createImageData(W, H);
    let raf = 0;
    let last = performance.now();
    let frames = 0;
    let fpsAcc = 0;
    let fps = 0;

    const fft1d = (
      re: Float64Array | Float32Array,
      im: Float64Array | Float32Array,
      n: number,
    ) => {
      for (let i = 1, j = 0; i < n; i++) {
        let bit = n >> 1;
        for (; j & bit; bit >>= 1) j ^= bit;
        j ^= bit;
        if (i < j) {
          const tr = re[i];
          re[i] = re[j];
          re[j] = tr;
          const ti = im[i];
          im[i] = im[j];
          im[j] = ti;
        }
      }
      for (let len = 2; len <= n; len <<= 1) {
        const ang = (-2 * Math.PI) / len;
        const wr = Math.cos(ang);
        const wi = Math.sin(ang);
        for (let i = 0; i < n; i += len) {
          let cr = 1;
          let ci = 0;
          for (let k = 0; k < len / 2; k++) {
            const ur = re[i + k];
            const ui = im[i + k];
            const vr =
              re[i + k + len / 2] * cr - im[i + k + len / 2] * ci;
            const vi =
              re[i + k + len / 2] * ci + im[i + k + len / 2] * cr;
            re[i + k] = ur + vr;
            im[i + k] = ui + vi;
            re[i + k + len / 2] = ur - vr;
            im[i + k + len / 2] = ui - vi;
            const ncr = cr * wr - ci * wi;
            ci = cr * wi + ci * wr;
            cr = ncr;
          }
        }
      }
    };

    const tick = () => {
      raf = requestAnimationFrame(tick);
      const s = state.current;
      const P = paramsRef.current;
      const now = performance.now();
      const dts = Math.min(0.05, (now - last) / 1000);
      last = now;
      frames++;
      fpsAcc += dts;
      if (fpsAcc > 0.5) {
        fps = frames / fpsAcc;
        frames = 0;
        fpsAcc = 0;
      }

      // ---- step ----
      if (!P.paused) {
        const sub = Math.max(1, Math.round(P.speedMul));
        for (let q = 0; q < sub; q++) {
          const dt = (DT * P.speedMul) / sub;
          s.fx.fill(0);
          s.fy.fill(0);
          // stirrer
          if (P.forced && P.stirrer) {
            s.t += 0;
            const cores = [
              [W * 0.3, H * 0.38],
              [W * 0.7, H * 0.38],
              [W * 0.5, H * 0.66],
              [W * 0.15, H * 0.75],
              [W * 0.85, H * 0.75],
            ];
            for (let sc = 0; sc < cores.length; sc++) {
              const cx = cores[sc][0];
              const cy = cores[sc][1];
              const R = 12;
              const str =
                14 * (sc % 2 === 0 ? 1 : -1) * Math.sin(s.t * 0.8 + sc);
              for (let j = 0; j < H; j++) {
                for (let i = 0; i < W; i++) {
                  const di = i - Math.floor(cx);
                  const dj = j - Math.floor(cy);
                  const d2 = di * di + dj * dj;
                  if (d2 < R * R) {
                    const fall = Math.exp((-d2 / (R * R)) * 0.3);
                    s.fx[IX(i, j)] +=
                      (-str * dj * fall) / Math.max(R, 1);
                    s.fy[IX(i, j)] +=
                      (str * di * fall) / Math.max(R, 1);
                  }
                }
              }
            }
          }
          // mouse force
          if (P.forced && mouse.current.down) {
            const r = canvas.getBoundingClientRect();
            const mx = ((mouse.current.x - r.left) / r.width) * W;
            const my = ((mouse.current.y - r.top) / r.height) * H;
            const mpx = ((mouse.current.px - r.left) / r.width) * W;
            const mpy = ((mouse.current.py - r.top) / r.height) * H;
            const velX = (mx - mpx) * 0.08;
            const velY = (my - mpy) * 0.08;
            const R = 9;
            const ci = Math.round(mx);
            const cj = Math.round(my);
            for (let j = cj - R; j <= cj + R; j++) {
              if (j < 0 || j >= H) continue;
              for (let i = ci - R; i <= ci + R; i++) {
                const di = i - ci;
                const dj = j - cj;
                const d2 = di * di + dj * dj;
                if (d2 > R * R) continue;
                const fall = Math.exp((-d2 / (R * R)) * 0.35);
                s.fx[IX(wrap(i, W), j)] += velX * fall;
                s.fy[IX(wrap(i, W), j)] += velY * fall;
              }
            }
          }
          // drag
          if (P.forced) {
            for (let c = 0; c < W * H; c++) {
              s.fx[c] -= 0.02 * s.u[c];
              s.fy[c] -= 0.02 * s.v[c];
            }
          }
          // confinement
          curl();
          if (P.confinement > 0) {
            for (let j = 0; j < H; j++) {
              for (let i = 0; i < W; i++) {
                const c = IX(i, j);
                const gx =
                  (Math.abs(s.w[IX(wrap(i + 1, W), j)]) -
                    Math.abs(s.w[IX(wrap(i - 1, W), j)])) *
                  0.5;
                const gy =
                  (Math.abs(s.w[IX(i, wrap(j + 1, H))]) -
                    Math.abs(s.w[IX(i, wrap(j - 1, H))])) *
                  0.5;
                const len = Math.sqrt(gx * gx + gy * gy) + 1e-9;
                s.fx[c] += P.confinement * dt * (gy / len) * s.w[c];
                s.fy[c] -= P.confinement * dt * (gx / len) * s.w[c];
              }
            }
          }
          for (let c = 0; c < W * H; c++) {
            s.u[c] += s.fx[c] * dt;
            s.v[c] += s.fy[c] * dt;
          }
          advect(dt);
          diffuse(dt);
          project();
          s.t += dt;
        }
        moveParticles(DT * P.speedMul);
        if (frames % 6 === 0) computeSpectrum();
      }
      curl();
      render();
      renderSpectrum();
      // stats
      let E = 0;
      let Ens = 0;
      for (let c = 0; c < W * H; c++) {
        E += s.u[c] * s.u[c] + s.v[c] * s.v[c];
        Ens += s.w[c] * s.w[c];
      }
      E *= 0.5 / (W * H);
      Ens *= 0.5 / (W * H);
      const slope = fitSlope();
      const keff = Math.sqrt(Math.max(Ens, 1e-12) / Math.max(E, 1e-12));
      const uref = Math.sqrt(2 * Math.max(E, 1e-12));
      const re = uref / (keff * P.nu + 1e-12);
      onStats({
        t: s.t,
        E,
        enstrophy: Ens,
        reynolds: re > 1 ? re : 0,
        fps,
        slope,
      });
    };

    const curl = () => {
      const s = state.current;
      for (let j = 0; j < H; j++) {
        for (let i = 0; i < W; i++) {
          s.w[IX(i, j)] =
            (s.v[IX(wrap(i + 1, W), j)] - s.v[IX(wrap(i - 1, W), j)]) * 0.5 -
            (s.u[IX(i, wrap(j + 1, H))] - s.u[IX(i, wrap(j - 1, H))]) * 0.5;
        }
      }
    };

    const advect = (dt: number) => {
      const s = state.current;
      for (let j = 0; j < H; j++) {
        for (let i = 0; i < W; i++) {
          const c = IX(i, j);
          const x = i - dt * s.u[c];
          const y = j - dt * s.v[c];
          s.u2[c] = sample(s.u, x, y);
          s.v2[c] = sample(s.v, x, y);
        }
      }
      s.u.set(s.u2);
      s.v.set(s.v2);
    };

    const diffuse = (dt: number) => {
      const s = state.current;
      const a = dt * paramsRef.current.nu;
      if (a < 1e-7) return;
      for (let it = 0; it < 4; it++) {
        for (let j = 0; j < H; j++) {
          for (let i = 0; i < W; i++) {
            const c = IX(i, j);
            const l = s.u[IX(wrap(i - 1, W), j)];
            const r = s.u[IX(wrap(i + 1, W), j)];
            const b = s.u[IX(i, wrap(j - 1, H))];
            const t = s.u[IX(i, wrap(j + 1, H))];
            s.u2[c] = (s.u[c] + a * (l + r + b + t)) / (1 + 4 * a);
            const l2 = s.v[IX(wrap(i - 1, W), j)];
            const r2 = s.v[IX(wrap(i + 1, W), j)];
            const b2 = s.v[IX(i, wrap(j - 1, H))];
            const t2 = s.v[IX(i, wrap(j + 1, H))];
            s.v2[c] = (s.v[c] + a * (l2 + r2 + b2 + t2)) / (1 + 4 * a);
          }
        }
        s.u.set(s.u2);
        s.v.set(s.v2);
      }
    };

    const project = () => {
      const s = state.current;
      for (let j = 0; j < H; j++) {
        for (let i = 0; i < W; i++) {
          const c = IX(i, j);
          s.div[c] =
            0.5 *
            (s.u[IX(wrap(i + 1, W), j)] - s.u[IX(wrap(i - 1, W), j)] +
              s.v[IX(i, wrap(j + 1, H))] - s.v[IX(i, wrap(j - 1, H))]);
          s.p[c] = 0;
        }
      }
      for (let it = 0; it < 28; it++) {
        for (let j = 0; j < H; j++) {
          for (let i = 0; i < W; i++) {
            const c = IX(i, j);
            const l = s.p[IX(wrap(i - 1, W), j)];
            const r = s.p[IX(wrap(i + 1, W), j)];
            const b = s.p[IX(i, wrap(j - 1, H))];
            const t = s.p[IX(i, wrap(j + 1, H))];
            s.p[c] = (l + r + b + t - s.div[c]) * 0.25;
          }
        }
      }
      for (let j = 0; j < H; j++) {
        for (let i = 0; i < W; i++) {
          const c = IX(i, j);
          s.u[c] -= 0.5 * (s.p[IX(wrap(i + 1, W), j)] - s.p[IX(wrap(i - 1, W), j)]);
          s.v[c] -= 0.5 * (s.p[IX(i, wrap(j + 1, H))] - s.p[IX(i, wrap(j - 1, H))]);
        }
      }
    };

    const moveParticles = (dt: number) => {
      const s = state.current;
      for (let n = 0; n < NP; n++) {
        const x = s.px[n];
        const y = s.py[n];
        let nx = x + sample(s.u, x, y) * dt * 8;
        let ny = y + sample(s.v, x, y) * dt * 8;
        nx = nx < 0 ? nx + W : nx >= W ? nx - W : nx;
        ny = ny < 0 ? ny + H : ny >= H ? ny - H : ny;
        s.px[n] = nx;
        s.py[n] = ny;
        s.page[n] += dt * 0.25;
      }
    };

    const computeSpectrum = () => {
      const s = state.current;
      s.kre.fill(0);
      s.kim.fill(0);
      s.kre2.fill(0);
      s.kim2.fill(0);
      for (let j = 0; j < SW; j++) {
        const sj = Math.floor((j * H) / SW);
        for (let i = 0; i < SW; i++) {
          const si = Math.floor((i * W) / SW);
          const c = IX(si, sj);
          s.kre[j * SW + i] = s.u[c];
          s.kre2[j * SW + i] = s.v[c];
        }
      }
      for (let axis = 0; axis < 2; axis++) {
        const colr = new Float64Array(SW);
        const coli = new Float64Array(SW);
        for (let i = 0; i < SW; i++) {
          for (let j = 0; j < SW; j++) {
            colr[j] = s.kre[j * SW + i];
            coli[j] = s.kim[j * SW + i];
          }
          fft1d(colr, coli, SW);
          for (let j = 0; j < SW; j++) {
            s.kre[j * SW + i] = colr[j];
            s.kim[j * SW + i] = coli[j];
          }
        }
        for (let j = 0; j < SW; j++) {
          fft1d(
            s.kre.subarray(j * SW, j * SW + SW) as Float64Array,
            s.kim.subarray(j * SW, j * SW + SW) as Float64Array,
            SW,
          );
        }
        for (let i = 0; i < SW; i++) {
          for (let j = 0; j < SW; j++) {
            colr[j] = s.kre2[j * SW + i];
            coli[j] = s.kim2[j * SW + i];
          }
          fft1d(colr, coli, SW);
          for (let j = 0; j < SW; j++) {
            s.kre2[j * SW + i] = colr[j];
            s.kim2[j * SW + i] = coli[j];
          }
        }
        for (let j = 0; j < SW; j++) {
          fft1d(
            s.kre2.subarray(j * SW, j * SW + SW) as Float64Array,
            s.kim2.subarray(j * SW, j * SW + SW) as Float64Array,
            SW,
          );
        }
      }
      s.EK.fill(0);
      const counts = new Float64Array(SW / 2);
      for (let j = 0; j < SW; j++) {
        const ky = j <= SW / 2 ? j : j - SW;
        for (let i = 0; i < SW; i++) {
          const kx = i <= SW / 2 ? i : i - SW;
          const k = Math.round(Math.sqrt(kx * kx + ky * ky));
          if (k >= 1 && k < SW / 2) {
            s.EK[k] +=
              s.kre[j * SW + i] ** 2 + s.kim[j * SW + i] ** 2 +
              s.kre2[j * SW + i] ** 2 + s.kim2[j * SW + i] ** 2;
            counts[k] += 1;
          }
        }
      }
      for (let k = 1; k < SW / 2; k++) {
        if (counts[k] > 0) {
          s.EK[k] = (s.EK[k] / counts[k]) * ((Math.PI * k * k) / (SW * SW)) * 2;
        }
        s.EKsm[k] = s.ready ? s.EKsm[k] * 0.7 + s.EK[k] * 0.3 : s.EK[k];
      }
      s.ready = true;
    };

    const fitSlope = () => {
      const s = state.current;
      let n = 0;
      let sx = 0;
      let sy = 0;
      let sxx = 0;
      let sxy = 0;
      for (let k = 6; k <= 20; k++) {
        if (s.EKsm[k] > 0) {
          const x = Math.log(k);
          const y = Math.log(s.EKsm[k]);
          n++;
          sx += x;
          sy += y;
          sxx += x * x;
          sxy += x * y;
        }
      }
      if (n < 5) return NaN;
      return (n * sxy - sx * sy) / (n * sxx - sx * sx);
    };

    const render = () => {
      const s = state.current;
      const P = paramsRef.current;
      curl();
      const d = img.data;
      let vmax = 0.12;
      if (P.view === "vort" || P.view === "schlieren") {
        for (let c = 0; c < W * H; c++) {
          if (Math.abs(s.w[c]) > vmax) vmax = Math.abs(s.w[c]);
        }
        vmax = Math.max(vmax, 1e-4);
      } else {
        for (let c = 0; c < W * H; c++) {
          const sp = Math.hypot(s.u[c], s.v[c]);
          if (sp > vmax) vmax = sp;
        }
      }
      const rgb = [0, 0, 0, 0];
      for (let j = 0; j < H; j++) {
        for (let i = 0; i < W; i++) {
          const c = IX(i, j);
          if (P.view === "vort") {
            const a = Math.max(-1, Math.min(1, s.w[c] / vmax));
            const t = Math.pow(Math.abs(a), 0.65);
            if (a >= 0) {
              rgb[0] = 20 + t * 211;
              rgb[1] = 21 + t * 148;
              rgb[2] = 25 + t * 44;
            } else {
              rgb[0] = 20 + t * 57;
              rgb[1] = 21 + t * 128;
              rgb[2] = 25 + t * 189;
            }
          } else if (P.view === "speed") {
            const sp = Math.hypot(s.u[c], s.v[c]) / (vmax + 1e-9);
            rgb[0] = 13 + sp * 190;
            rgb[1] = 15 + sp * 140;
            rgb[2] = 19 + sp * 40;
          } else {
            const gx = s.w[IX(wrap(i + 1, W), j)] - s.w[IX(wrap(i - 1, W), j)];
            const gy = s.w[IX(i, wrap(j + 1, H))] - s.w[IX(i, wrap(j - 1, H))];
            const sp = Math.min(
              1,
              Math.sqrt(gx * gx + gy * gy) / (vmax * 0.6 + 1e-9),
            );
            const inv = 1 - sp;
            rgb[0] = 20 + inv * 200;
            rgb[1] = 22 + inv * 200;
            rgb[2] = 26 + inv * 205;
          }
          rgb[3] = 255;
          const o = c * 4;
          d[o] = rgb[0];
          d[o + 1] = rgb[1];
          d[o + 2] = rgb[2];
          d[o + 3] = 255;
        }
      }
      const tmp = document.createElement("canvas");
      tmp.width = W;
      tmp.height = H;
      tmp.getContext("2d")!.putImageData(img, 0, 0);
      ctx.imageSmoothingEnabled = true;
      ctx.drawImage(tmp, 0, 0, canvas.width, canvas.height);
      if (P.particles) {
        ctx.fillStyle = "rgba(233,231,225,0.5)";
        for (let n = 0; n < NP; n++) {
          const age = s.page[n] % 1;
          ctx.globalAlpha = 0.15 + 0.45 * Math.sin(age * Math.PI);
          ctx.fillRect(
            (s.px[n] / W) * canvas.width,
            (s.py[n] / H) * canvas.height,
            1.6,
            1.6,
          );
        }
        ctx.globalAlpha = 1;
      }
      if (P.arrows) {
        ctx.strokeStyle = "rgba(211,169,69,0.75)";
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        const stepI = 16;
        for (let j = stepI / 2; j < H; j += stepI) {
          for (let i = stepI / 2; i < W; i += stepI) {
            const c = IX(i, j);
            const x0 = (i / W) * canvas.width;
            const y0 = (j / H) * canvas.height;
            const dx = s.u[c] * 6;
            const dy = s.v[c] * 6;
            if (Math.hypot(dx, dy) < 2) continue;
            ctx.moveTo(x0, y0);
            ctx.lineTo(x0 + dx * 8, y0 + dy * 8);
          }
        }
        ctx.stroke();
      }
    };

    const renderSpectrum = () => {
      const s = state.current;
      const wpx = specCanvas.width;
      const hpx = specCanvas.height;
      sctx.clearRect(0, 0, wpx, hpx);
      const padL = 44;
      const padB = 24;
      const padT = 8;
      const padR = 8;
      const x0 = padL;
      const y0 = hpx - padB;
      const kmin = 2;
      const kmax = 48;
      const emin = 1e-3;
      const emax = 3e4;
      const lx = (k: number) =>
        x0 +
        ((Math.log(k) - Math.log(kmin)) / (Math.log(kmax) - Math.log(kmin))) *
          (wpx - padL - padR);
      const ly = (e: number) =>
        y0 -
        ((Math.log(e) - Math.log(emin)) / (Math.log(emax) - Math.log(emin))) *
          (y0 - padT);
      sctx.strokeStyle = "#2e3340";
      sctx.lineWidth = 1;
      sctx.beginPath();
      sctx.moveTo(x0, padT);
      sctx.lineTo(x0, y0);
      sctx.lineTo(wpx - padR, y0);
      sctx.stroke();
      sctx.fillStyle = "#9aa0ac";
      sctx.font = "9px sans-serif";
      for (const k of [2, 5, 10, 20, 40]) {
        sctx.fillText(String(k), lx(k) - 4, y0 + 13);
      }
      for (const e of [1e-3, 1e0, 1e3]) {
        sctx.fillText(e.toExponential(0), 3, ly(e) + 3);
      }
      const anchors: [number, string][] = [
        [-5 / 3, "#4db3d6"],
        [-3, "#d46a5f"],
      ];
      for (const [pwr, col] of anchors) {
        const k0 = 8;
        const e0 = s.EKsm[k0] > 0 ? s.EKsm[k0] : 1e-6;
        sctx.strokeStyle = col;
        sctx.globalAlpha = 0.65;
        sctx.lineWidth = 1.2;
        sctx.beginPath();
        sctx.moveTo(lx(3), ly(e0 * Math.pow(3 / k0, pwr)));
        sctx.lineTo(lx(48), ly(e0 * Math.pow(48 / k0, pwr)));
        sctx.stroke();
        sctx.globalAlpha = 1;
      }
      sctx.fillStyle = "rgba(211,169,69,0.10)";
      sctx.fillRect(lx(6), padT, lx(20) - lx(6), y0 - padT);
      sctx.strokeStyle = "#d3a945";
      sctx.lineWidth = 1.8;
      sctx.beginPath();
      let started = false;
      for (let k = 2; k < SW / 2; k++) {
        if (s.EKsm[k] <= 0) continue;
        const X = lx(k);
        const Y = ly(s.EKsm[k]);
        if (!started) {
          sctx.moveTo(X, Y);
          started = true;
        } else {
          sctx.lineTo(X, Y);
        }
      }
      sctx.stroke();
    };

    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [canvasRef, specRef, onStats, sample, reset]);

  const pointerHandlers = {
    onPointerDown: (ev: React.PointerEvent) => {
      const el = ev.currentTarget;
      const r = el.getBoundingClientRect();
      mouse.current = {
        down: true,
        x: ev.clientX,
        y: ev.clientY,
        px: ev.clientX,
        py: ev.clientY,
      };
      void r;
      el.setPointerCapture(ev.pointerId);
    },
    onPointerMove: (ev: React.PointerEvent) => {
      mouse.current.px = mouse.current.x;
      mouse.current.py = mouse.current.y;
      mouse.current.x = ev.clientX;
      mouse.current.y = ev.clientY;
    },
    onPointerUp: () => {
      mouse.current.down = false;
    },
  };

  return { reset, pointerHandlers };
}
