module Main (main) where
import Text.Printf (printf)

pi' :: Double
pi' = pi
alpha :: Double
alpha = sqrt 168 / (2 * pi')

main :: IO ()
main = do
  putStrLn "=== Section 2: Preprint NSE (Haskell) ==="
  printf "alpha = %.15e\n" alpha
