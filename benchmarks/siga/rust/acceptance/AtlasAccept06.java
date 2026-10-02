import br.gov.jfrj.siga.util.FreemarkerIndent;
import br.gov.jfrj.siga.util.FreemarkerMarker;
import java.util.ArrayList;

/**
 * Aceite isolado de SIGA-REAL-06 ("Preservar literais no ciclo FreeMarker e HTML").
 * Compila com javac contra as fontes da base (+ jsoup do repo Maven local),
 * sem Maven/JUnit/rede. Qualquer FAIL devolve exit != 0.
 *
 * Cobre o ciclo de conversao FreeMarker -> HTML -> FreeMarker
 * (convertFtl2Html/convertHtml2Ftl) com cifroes, barras invertidas e aspas
 * escapadas, mais os casos ja suportados do IndentTest como regressao.
 * O indentador completo (tidy/jsoup) fica fora deste aceite.
 */
public class AtlasAccept06 {
  static int passed = 0;
  static int failed = 0;

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

  static String roundTrip(String ftl) {
    ArrayList<String> lftl = new ArrayList<String>();
    String html = FreemarkerIndent.convertFtl2Html(ftl, lftl);
    return FreemarkerIndent.convertHtml2Ftl(html, lftl);
  }

  public static void main(String[] args) {
    // Aspas duplas escapadas no meio do literal.
    check("rt-escaped-dquote", "[#if x==\"a\\\"b\"]ok[/#if]",
        () -> roundTrip("[#if x==\"a\\\"b\"]ok[/#if]"));
    // Aspa escapada imediatamente antes do fechamento: nao pode estourar.
    check("rt-escaped-dquote-close", "[#if x==\"a\\\"\"]ok[/#if]",
        () -> roundTrip("[#if x==\"a\\\"\"]ok[/#if]"));
    // Aspas simples escapadas.
    check("rt-escaped-squote", "[#if x=='it\\'s']ok[/#if]",
        () -> roundTrip("[#if x=='it\\'s']ok[/#if]"));
    // Caminho Windows com barras duplas.
    check("rt-winpath-double", "[#assign p=\"C:\\\\temp\\\\file\" /]",
        () -> roundTrip("[#assign p=\"C:\\\\temp\\\\file\" /]"));
    // Caminho Windows com barras simples.
    check("rt-winpath-single", "[#assign p=\"C:\\temp\\new\" /]",
        () -> roundTrip("[#assign p=\"C:\\temp\\new\" /]"));
    // Cifrao literal ja suportado (regressao).
    check("rt-dollar", "[#if v==\"$100\"]ok[/#if]",
        () -> roundTrip("[#if v==\"$100\"]ok[/#if]"));
    // Diretivas consecutivas ja suportadas (regressao).
    check("rt-consecutive", "[#if][#else][/#if]",
        () -> roundTrip("[#if][#else][/#if]"));
    // Casos do IndentTest ja suportados (regressao, sem tidy).
    check("marker-simple", "{{fm}}[#teste]{{/fm}}",
        () -> new FreemarkerMarker("[#teste]").run());
    check("convert-open", "<!--fm-open=\"1\"-->",
        () -> FreemarkerIndent.convertFtl2Html("[#entrevista]", new ArrayList<String>()));
    check("convert-roundtrip", "[#test]", () -> roundTrip("[#test]"));

    System.out.println("AtlasAccept06: " + passed + "/" + (passed + failed) + " passed");
    if (failed > 0) {
      System.exit(1);
    }
  }
}
