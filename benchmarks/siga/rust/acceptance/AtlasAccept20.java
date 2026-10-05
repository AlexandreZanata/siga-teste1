import br.gov.jfrj.siga.base.util.Texto;

/**
 * Aceite isolado de SIGA-REAL-20 ("entidades HTML sem acento restante").
 * Compila com javac contra as fontes da base, sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 *
 * Contrato: removeAcentoHTML troca TODA entidade acentuada por ASCII puro —
 * '&agrave;' vira 'a', como as onze irmas. Texto sem entidade passa intacto.
 */
public class AtlasAccept20 {
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

  public static void main(String[] args) {
    check("aacute", "a", Texto.removeAcentoHTML("&aacute;"));
    check("eacute", "e", Texto.removeAcentoHTML("&eacute;"));
    check("iacute", "i", Texto.removeAcentoHTML("&iacute;"));
    check("oacute", "o", Texto.removeAcentoHTML("&oacute;"));
    check("uacute", "u", Texto.removeAcentoHTML("&uacute;"));
    check("agrave", "a", Texto.removeAcentoHTML("&agrave;"));
    check("acirc", "a", Texto.removeAcentoHTML("&acirc;"));
    check("ecirc", "e", Texto.removeAcentoHTML("&ecirc;"));
    check("ocirc", "o", Texto.removeAcentoHTML("&ocirc;"));
    check("atilde", "a", Texto.removeAcentoHTML("&atilde;"));
    check("otilde", "o", Texto.removeAcentoHTML("&otilde;"));
    check("mixed", "cafe a la", Texto.removeAcentoHTML("caf&eacute; &agrave; la"));
    check("plain", "abc 123", Texto.removeAcentoHTML("abc 123"));
    check("null", null, Texto.removeAcentoHTML(null));

    System.out.println("AtlasAccept20: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
