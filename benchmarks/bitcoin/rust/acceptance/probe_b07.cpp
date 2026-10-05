// Sonda do avaliador — BTC-REAL-07 (compilada contra o workspace, nunca
// contra a referência). Casos comportamentais de ParseByteUnits; exit 0 se
// todos passam, exit 1 em qualquer FAIL. Sem Boost, sem daemon, sem rede.
#include <cstdint>
#include <cstdio>
#include <optional>
#include <string>
#include <string_view>
#include <util/strencodings.h>

static int failures = 0;

static void check(const char* name, std::string_view in, ByteUnit def,
                  bool expect_ok, uint64_t expect_val) {
    auto got = ParseByteUnits(in, def);
    bool ok = (got.has_value() == expect_ok) && (!expect_ok || *got == expect_val);
    std::printf("%s %s: ParseByteUnits(\"%.*s\") -> %s\n", ok ? "PASS" : "FAIL", name,
                (int)in.size(), in.data(),
                got.has_value() ? std::to_string(*got).c_str() : "nullopt");
    if (!ok) ++failures;
}

int main() {
    check("B-explicit-K", "10B", ByteUnit::K, true, 10);
    check("B-explicit-m", "10B", ByteUnit::m, true, 10);
    check("B-zero", "0B", ByteUnit::K, true, 0);
    check("B-bare-rejected", "B", ByteUnit::NOOP, false, 0);
    check("B-decimal-rejected", "1.5B", ByteUnit::NOOP, false, 0);
    check("B-negative-rejected", "-3B", ByteUnit::NOOP, false, 0);
    check("B-overflow-rejected", "99999999999999999999B", ByteUnit::NOOP, false, 0);
    check("plain-preserved", "42", ByteUnit::NOOP, true, 42);
    check("k-preserved", "1k", ByteUnit::NOOP, true, 1000);
    check("K-preserved", "1K", ByteUnit::NOOP, true, 1024);
    check("m-preserved", "2m", ByteUnit::NOOP, true, 2000000);
    check("M-preserved", "2M", ByteUnit::NOOP, true, 2ULL << 20);
    check("g-preserved", "3g", ByteUnit::NOOP, true, 3000000000ULL);
    check("G-preserved", "3G", ByteUnit::NOOP, true, 3ULL << 30);
    check("t-preserved", "4t", ByteUnit::NOOP, true, 4000000000000ULL);
    check("T-preserved", "4T", ByteUnit::NOOP, true, 4ULL << 40);
    check("empty-rejected", "", ByteUnit::NOOP, false, 0);
    if (failures) {
        std::printf("%d case(s) FAILED\n", failures);
        return 1;
    }
    std::printf("all cases passed\n");
    return 0;
}
