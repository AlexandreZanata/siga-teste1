import br.gov.jfrj.siga.base.AplicacaoException;
import br.gov.jfrj.siga.base.util.CPFUtils;

/**
 * Aceite isolado de SIGA-REAL-03 ("Contrato do CPF com mascara exata").
 * Compila com javac contra as fontes da base (+commons-lang), sem Maven/JUnit/rede.
 * Qualquer FAIL devolve exit != 0.
 */
public class AtlasAccept03 {
  static int passed = 0;
  static int failed = 0;

  static void checkAccept(String name, String cpf) {
    try {
      CPFUtils.efetuaValidacaoSimples(cpf);
      passed++;
      System.out.println("PASS " + name);
    } catch (Throwable t) {
      failed++;
      System.out.println("FAIL " + name + " expected=aceito threw=" + t.getClass().getName());
    }
  }

  static void checkReject(String name, String cpf) {
    try {
      CPFUtils.efetuaValidacaoSimples(cpf);
      failed++;
      System.out.println("FAIL " + name + " expected=AplicacaoException actual=aceito");
    } catch (AplicacaoException t) {
      passed++;
      System.out.println("PASS " + name);
    } catch (Throwable t) {
      failed++;
      System.out.println("FAIL " + name + " expected=AplicacaoException threw=" + t.getClass().getName());
    }
  }

  static void checkLong(String name, String cpf, long expected) {
    try {
      Long actual = CPFUtils.getLongValueValidaSimples(cpf);
      if (actual != null && actual.longValue() == expected) {
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
    // Criterio 1: 11 digitos e mascara correta aceitos.
    checkAccept("plain-ok", "12345678909");
    checkAccept("mask-ok", "123.456.789-09");
    // Criterio 2: pontuacao deslocada rejeitada.
    checkReject("misplaced-punct", "12.3456.789-09");
    // Formato estrito: so digitos ASCII.
    checkReject("nonascii-digits", "١٢٣٤٥٦٧٨٩٠١");
    checkReject("letter", "1234567890a");
    checkReject("blank", "   ");
    checkReject("null", null);
    checkReject("wrong-length", "111111111111");
    // Criterio 3: mesmo contrato no getLongValue, com zeros iniciais.
    checkLong("long-leading-zero", "00123456789", 123456789L);
    checkLong("long-masked", "123.456.789-09", 12345678909L);

    System.out.println("AtlasAccept03: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
