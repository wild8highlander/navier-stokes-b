module Main (main) where
import Text.Printf (printf)

main :: IO ()
main = do
  putStrLn "=== Section 5: Klein Attractor (Haskell) ==="
  printf "box_dim = %.15e\n" (log 168 / log 7)
