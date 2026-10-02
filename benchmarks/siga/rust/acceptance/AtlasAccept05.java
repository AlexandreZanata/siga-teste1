import br.gov.jfrj.siga.base.util.SetUtils;
import java.util.Collections;
import java.util.HashSet;
import java.util.Set;

/**
 * Aceite isolado de SIGA-REAL-05 ("Operacoes de conjuntos sem Comparable").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 */
public class AtlasAccept05 {
  static int passed = 0;
  static int failed = 0;

  /** Valor com equals/hashCode e SEM Comparable: TreeSet quebra aqui. */
  static final class Box {
    final String v;

    Box(String v) {
      this.v = v;
    }

    public boolean equals(Object o) {
      return o instanceof Box && ((Box) o).v.equals(v);
    }

    public int hashCode() {
      return v.hashCode();
    }
  }

  static Set<Box> setOf(String... vs) {
    Set<Box> s = new HashSet<Box>();
    for (String v : vs) {
      s.add(new Box(v));
    }
    return s;
  }

  interface Probe {
    Object run() throws Throwable;
  }

  static void check(String name, Object expected, Probe probe) {
    try {
      Object actual = probe.run();
      boolean ok = expected == null ? actual == null : expected.equals(actual);
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

  public static void main(String[] args) {
    final Set<Box> left = setOf("a", "b");
    final Set<Box> right = setOf("b", "c");
    final Set<Box> leftCopy = setOf("a", "b");
    final Set<Box> rightCopy = setOf("b", "c");

    // Uniao por valor, sem ClassCastException.
    check("union-values", setOf("a", "b", "c"), () -> SetUtils.union(left, right));
    // Intersecao por valor.
    check("intersection-values", setOf("b"), () -> SetUtils.intersection(left, right));
    // Diferenca por valor.
    check("difference-values", setOf("a"), () -> SetUtils.difference(left, right));
    // Diferenca simetrica por valor.
    check("symdiff-values", setOf("a", "c"), () -> SetUtils.symDifference(left, right));
    // Conjuntos vazios funcionam.
    check("union-empty", setOf(), () -> SetUtils.union(setOf(), setOf()));
    // Subtraendo vazio preserva o minuendo.
    check("difference-empty", setOf("a", "b"), () -> SetUtils.difference(setOf("a", "b"), setOf()));
    // Entradas imutaveis funcionam.
    check("union-unmodifiable", setOf("a", "b", "c"),
        () -> SetUtils.union(Collections.unmodifiableSet(setOf("a", "b")),
            Collections.unmodifiableSet(setOf("b", "c"))));
    // Entradas nao sao modificadas.
    check("inputs-unchanged", Boolean.TRUE, () -> {
      SetUtils.union(left, right);
      SetUtils.difference(left, right);
      return left.equals(leftCopy) && right.equals(rightCopy);
    });
    // Subconjunto / superconjunto por valor.
    check("subset-true", Boolean.TRUE, () -> SetUtils.isSubset(setOf("a"), setOf("a", "b")));
    check("superset-false", Boolean.FALSE, () -> SetUtils.isSuperset(setOf("a"), setOf("a", "b")));

    System.out.println("AtlasAccept05: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
