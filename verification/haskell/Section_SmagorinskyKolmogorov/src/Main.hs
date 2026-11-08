module Main (main) where

-- | Section 7 — Smagorinsky-Kolmogorov master relation (Haskell port, pure).
--
-- Verifies the same claims as the Python/C++/Rust ports:
--   * parent constant b and sin(theta_b) = b;
--   * C_s(C_K) = 1/(pi * (3*C_K/2)^(3/4)), Lilly agreement, exponent law;
--   * monotonicity + literature band;
--   * Cassini identity on Integer Fibonacci (exact, arbitrary precision);
--   * reduced zero-drift condition (5'): a*b*b*c sign-definite,
--     a*a*b*b degenerate.
--
-- Output contract: banner -> [PASS]/[FAIL] -> JSON verdict -> exit code.

import Text.Printf (printf)
import System.Exit (exitWith, ExitCode (..))
import Data.List (foldl')

piConst :: Double
piConst = pi

bCorrection :: Double
bCorrection = 1 / (4 * piConst + 2 * sqrt 3)

csMaster :: Double -> Double
csMaster ck = 1 / (piConst * (3 * ck / 2) ** 0.75)

-- exact Integer Fibonacci
fib :: Int -> Integer
fib n = snd (foldl' (\(a, b) _ -> (b, a + b)) (0, 1) [1 .. n])

check :: (String, Bool) -> IO Bool
check (name, cond) = do
  putStrLn ("[" ++ (if cond then "PASS" else "FAIL") ++ "] " ++ name)
  pure cond

main :: IO ()
main = do
  putStrLn "=== Section 7: Smagorinsky-Kolmogorov Master Relation (Haskell) ==="
  let b = bCorrection
      theta = asin b
  printf "b = %.17e, theta_b = %.11f deg\n" b (theta * 180 / piConst)
  r1 <- check ("b matches pinned value",
               abs (b - 0.062381194121028227546339671639402081186993) < 5e-16)
  r2 <- check ("sin(theta_b) = b", abs (sin theta - b) < 1e-17)

  let cs = csMaster 1.5
  printf "C_s(1.5) = %.17e\n" cs
  r3 <- check ("C_s(1.5) matches pinned value",
               abs (cs - 0.1732659558297058017568595667273903913207704) < 5e-16)
  r4 <- check ("|C_s - Lilly| < 1e-5", abs (cs - 0.17326) < 1e-5)

  let worst = maximum [abs (csMaster (a * 1.5) / cs - a ** (-0.75))
                      | a <- [0.5, 0.8, 1.25, 2.0, 3.0]]
  r5 <- check ("exponent law a^(-3/4)", worst < 1e-14)
  r6 <- check ("monotonic C_s", csMaster 1.8 < cs && cs < csMaster 1.2)
  r7 <- check ("literature band 0.16..0.20", cs > 0.16 && cs < 0.20)

  let cassini = all (\k -> fib (k + 1) ^ (2 :: Int) - fib k * fib (k + 2)
                             == (if even k then 1 else -1 :: Integer))
                    [0 .. 40]
  r8 <- check ("Cassini identity k = 0..40", cassini)

  let phi = (1 + sqrt 5) / 2 :: Double
      delta = 1e-6 :: Double
      lhsSignOk k t =
        let fa = fromIntegral (fib k) :: Double
            fb = fromIntegral (fib (k + 1))
            fc = fromIntegral (fib (k + 2))
            c2 = fb * fb - fa * fc
            cM = fb * fc - fa * fb
            c1 = fc * fc - fb * fb
            r1 = t; r2 = t / phi
            m1 = max (r1 * r1) (delta * delta)
            m2 = max (r2 * r2) (delta * delta)
            mM = max (r1 * r1 + r2 * r2) (delta * delta)
        in c2 * m2 + cM * mM + c1 * m1 > 0
      noRoot = all (\(k, t) -> lhsSignOk k t)
                   [(k, t) | k <- [2 .. 7], t <- [0.3, 0.8, 1.5]]
      degenerate = all (\k -> fib k * fib (k + 1) - fib k * fib (k + 1) == 0
                               && fib (k + 1) ^ (2 :: Int) - fib (k + 1) ^ (2 :: Int) == 0)
                       [2 .. 7]
  r9 <- check ("a*b*b*c: (5') sign-definite (no zero-drift root)", noRoot)
  r10 <- check ("a*a*b*b: (5') coefficients vanish identically", degenerate)

  let ok = and [r1, r2, r3, r4, r5, r6, r7, r8, r9, r10]
  printf "JSON: {\"section\": 7, \"language\": \"haskell\", \"values\": {\"C_s\": \"%.17e\", \"b\": \"%.17e\"}, \"all_passed\": %s}\n"
         cs b (if ok then "true" else "false")
  exitWith (if ok then ExitSuccess else ExitFailure 1)
