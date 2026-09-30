module Main (main) where
import Text.Printf (printf)

gamma1, gamma2, gamma3 :: Double
gamma1 = 14.134725141734693
gamma2 = 21.022039638771555
gamma3 = 25.010857580145688

main :: IO ()
main = do
  putStrLn "=== Section 6: Riemann Zeros (Haskell) ==="
  printf "gamma_1 = %.15e\n" gamma1
