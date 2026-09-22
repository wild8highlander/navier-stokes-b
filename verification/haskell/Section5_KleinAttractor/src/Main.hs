module Main (main) where
import Text.Printf (printf)

-- Hausdorff (box-counting) dimension of the Kleinian limit set:
-- log(N) / log(1/eps) computed as log 168 / log 7.
box_dim :: Double
box_dim = log 168 / log 7

main :: IO ()
main = do
  putStrLn "=== Section 5: Klein Attractor (Haskell) ==="
  printf "box_dim = %.15e\n" box_dim
