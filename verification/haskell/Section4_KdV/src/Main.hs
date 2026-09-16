module Main (main) where
import Text.Printf (printf)

main :: IO ()
main = do
  putStrLn "=== Section 4: KdV (Haskell) ==="
  let u_peak = 0.5 :: Double
  printf "soliton peak = %.15e\n" u_peak
