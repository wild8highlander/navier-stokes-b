module Main (main) where
import Text.Printf (printf)

pi' :: Double
pi' = pi

bCorrection :: Double
bCorrection = pi' / (4 * pi'^2 + 2 * pi' * sqrt 3)

main :: IO ()
main = do
  putStrLn "=== Section 1: Correction b (Haskell) ==="
  printf "b = %.15e\n" bCorrection
