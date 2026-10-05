import br.gov.jfrj.siga.base.util.Texto;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

/**
 * Aceite isolado de SIGA-REAL-19 ("lista por extenso sem consumir a entrada").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 *
 * Contrato: mesma renderizacao de antes ("a, b e c"), sem modificar a lista
 * recebida — chamadores como ExRef.getSigla/getFolha passam listas vivas.
 */
public class AtlasAccept19 {
  static int passed = 0;
  static int failed = 0;

  static void check(String name, Object expected, Object actual) {
    boolean ok = expected == null ? actual == null : expected.equals(actual);
    if (ok) {
      passed++;
      System.out.println("PASS " + name);
    } else {
      failed++;
      System.out.println("FAIL " + name + " expected=<" + expected + "> actual=<" + actual + ">");
    }
  }

  static List<String> lista(String... itens) {
    return new ArrayList<String>(Arrays.asList(itens));
  }

  public static void main(String[] args) {
    // Trio: renderizacao com virgula e 'e'.
    List<String> trio = lista("a", "b", "c");
    check("render-trio", "a, b e c", Texto.stringsSeparadarComVirgulaEE(trio));
    check("intact-trio", "[a, b, c]", trio.toString());

    // Unitario: sem separador.
    List<String> um = lista("so");
    check("render-single", "so", Texto.stringsSeparadarComVirgulaEE(um));
    check("intact-single", "[so]", um.toString());

    // Par: so 'e'.
    List<String> par = lista("a", "b");
    check("render-pair", "a e b", Texto.stringsSeparadarComVirgulaEE(par));
    check("intact-pair", "[a, b]", par.toString());

    // Vazia: null como antes (contrato preservado), nada a consumir.
    List<String> vazia = lista();
    check("render-empty", null, Texto.stringsSeparadarComVirgulaEE(vazia));
    check("intact-empty", "[]", vazia.toString());

    // Repetidos: cada ocorrencia rende um termo.
    List<String> dup = lista("x", "x");
    check("render-dup", "x e x", Texto.stringsSeparadarComVirgulaEE(dup));
    check("intact-dup", "[x, x]", dup.toString());

    System.out.println("AtlasAccept19: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
