import br.gov.jfrj.siga.base.util.SetUtils;
import java.util.Collections;
import java.util.HashSet;
import java.util.Objects;
import java.util.Set;

/**
 * Aceite isolado de SIGA-REAL-05 ("Operacoes de conjuntos sem Comparable").
 *
 * <p>Compila com {@code javac} contra as fontes originais, sem Maven, sem JUnit, sem rede.
 * {@code Box} implementa equals/hashCode sem Comparable. Cada caso imprime {@code PASS} ou
 * {@code FAIL}; qualquer falha devolve codigo diferente de zero.
 */
public class AtlasAccept05 {
  static int passed = 0;
  static int failed = 0;

  /** Valor com igualdade por conteudo e sem ordem natural. */
  static final class Box {
    final int id;

    Box(int id) {
      this.id = id;
    }

    @Override
    public boolean equals(Object o) {
      return o instanceof Box && ((Box) o).id == id;
    }

    @Override
    public int hashCode() {
      return Integer.hashCode(id);
    }

    @Override
    public String toString() {
      return "Box(" + id + ")";
    }
  }

  interface Probe {
    Object run() throws Throwable;
  }

  static void check(String name, Object expected, Probe probe) {
    try {
      Object actual = probe.run();
      boolean ok = Objects.equals(expected, actual);
      if (ok) {
        passed++;
        System.out.println("PASS " + name);
      } else {
        failed++;
        System.out.println("FAIL " + name + " expected=<" + expected + "> actual=<" + actual + ">");
      }
    } catch (Throwable t) {
      failed++;
      System.out.println("FAIL " + name + " threw=" + t.getClass().getName() + ": " + t.getMessage());
    }
  }

  static Set<Box> boxes(int... ids) {
    Set<Box> s = new HashSet<>();
    for (int id : ids) {
      s.add(new Box(id));
    }
    return s;
  }

  public static void main(String[] args) {
    // Criterio 1: uniao de nao Comparable funciona sem ClassCastException.
    check("union-singleton", boxes(1),
        () -> SetUtils.union(Set.of(new Box(1)), Set.of()));
    // Criterio 2: operacoes respeitam igualdade por valor (nao identidade).
    check("union-value-equality", boxes(1),
        () -> SetUtils.union(Set.of(new Box(1)), Set.of(new Box(1))));
    check("intersection-value-equality", boxes(2),
        () -> SetUtils.intersection(boxes(1, 2), boxes(2, 3)));
    check("difference-value-equality", boxes(1),
        () -> SetUtils.difference(boxes(1, 2), boxes(2, 3)));
    check("symdiff-value-equality", boxes(1, 3),
        () -> SetUtils.symDifference(boxes(1, 2), boxes(2, 3)));
    // Criterio 3: vazios e imutaveis funcionam.
    check("empty-union", Set.of(), () -> SetUtils.union(Set.of(), Set.of()));
    check("immutable-inputs", boxes(1),
        () -> SetUtils.union(Collections.unmodifiableSet(boxes(1)),
            Collections.unmodifiableSet(boxes())));
    // Entradas permanecem inalteradas.
    check("inputs-unmodified", true, () -> {
      Set<Box> a = boxes(1, 2);
      Set<Box> b = boxes(2, 3);
      Set<Box> aBefore = new HashSet<>(a);
      Set<Box> bBefore = new HashSet<>(b);
      SetUtils.union(a, b);
      SetUtils.intersection(a, b);
      SetUtils.difference(a, b);
      SetUtils.symDifference(a, b);
      return a.equals(aBefore) && b.equals(bBefore);
    });

    System.out.println("AtlasAccept05: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
