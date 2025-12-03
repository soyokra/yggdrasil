package java.bytecode;

/**
 * 异常处理示例 - 演示try-catch-finally、throws声明
 */
public class ExceptionExample {
    
    // try-catch-finally示例
    public void exceptionExample() {
        try {
            int result = 10 / 0;
        } catch (ArithmeticException e) {
            System.out.println("Caught: " + e.getMessage());
        } catch (Exception e) {
            System.out.println("Caught general exception");
        } finally {
            System.out.println("Finally block");
        }
    }
    
    // throws声明示例
    public void exceptionThrows() throws IllegalArgumentException {
        throw new IllegalArgumentException("Test exception");
    }
    
    // 多个catch块示例
    public void multipleCatchExample() {
        try {
            String str = null;
            int length = str.length();
        } catch (NullPointerException e) {
            System.out.println("NullPointerException: " + e.getMessage());
        } catch (Exception e) {
            System.out.println("General exception: " + e.getMessage());
        }
    }
}

