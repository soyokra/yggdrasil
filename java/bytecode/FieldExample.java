package java.bytecode;

/**
 * 字段示例 - 演示各种类型的字段定义
 */
public class FieldExample {
    
    // 静态字段
    public static final int STATIC_FINAL_INT = 100;
    private static String staticField = "static";
    
    // 实例字段 - 基本类型
    private int intField;
    private long longField;
    private double doubleField;
    private boolean booleanField;
    private char charField;
    
    // 实例字段 - 对象类型
    private String stringField;
    
    // 实例字段 - 数组
    private int[] intArray;
    private String[] stringArray;
    
    // final字段
    private final String finalField = "final";
    
    public FieldExample() {
        this.intField = 0;
    }
    
    public int getIntField() {
        return intField;
    }
    
    public void setIntField(int intField) {
        this.intField = intField;
    }
}

