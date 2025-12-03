package java.bytecode;

/**
 * 枚举类型示例
 */
public enum Status {
    PENDING("待处理"),
    PROCESSING("处理中"),
    COMPLETED("已完成"),
    FAILED("失败");
    
    private final String description;
    
    Status(String description) {
        this.description = description;
    }
    
    public String getDescription() {
        return description;
    }
}

