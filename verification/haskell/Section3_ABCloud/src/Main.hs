module Main (main) where
import Text.Printf (printf)

pi' :: Double
pi' = pi

main :: IO ()
main = do
  putStrLn "=== Section 3: AB-Cloud (Haskell) ==="
  printf "peierls = %.15e\n" (cos (2 * pi' / 7))
