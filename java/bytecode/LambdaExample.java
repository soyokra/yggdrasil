package java.bytecode;

import java.util.function.Function;
import java.util.function.Predicate;

/**
 * Lambda表达式示例 - 演示Java 8 Lambda表达式
 */
public class LambdaExample {
    
    // Lambda表达式示例
    public void lambdaExample() {
        Function<String, Integer> func = s -> s.length();
        int length = func.apply("Hello");
        System.out.println("Length: " + length);
    }
    
    // Lambda表达式 - 多行
    public void lambdaMultiLineExample() {
        Function<String, String> func = s -> {
            String upper = s.toUpperCase();
            return upper + "!";
        };
        String result = func.apply("hello");
        System.out.println(result);
    }
    
    // Lambda表达式 - Predicate
    public void lambdaPredicateExample() {
        Predicate<Integer> isEven = n -> n % 2 == 0;
        boolean result = isEven.test(10);
        System.out.println("Is 10 even? " + result);
    }
}

